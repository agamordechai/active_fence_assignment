"""Complete data processing pipeline: collect -> enrich -> score"""
import logging
import json
import os
from pathlib import Path
from datetime import datetime

from src.collectors.reddit_scraper import RedditScraper
from src.enrichers.user_enricher import UserEnricher
from src.scorers.hate_speech_scorer import HateSpeechScorer
from src.api_client import APIClient

logger = logging.getLogger(__name__)


class DataPipeline:
    """Complete data processing pipeline"""

    def __init__(self):
        self.scraper = RedditScraper(rate_limit_delay=2.0)
        self.enricher = UserEnricher()
        self.scorer = HateSpeechScorer()
        self.api_client = APIClient()

        # Create output directories
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)

    def run_full_pipeline(self, subreddits: list, posts_per_subreddit: int = 25,
                         max_users_to_enrich: int = 20):
        """
        Run complete pipeline: collection -> enrichment -> scoring

        Args:
            subreddits: List of subreddit names to collect from
            posts_per_subreddit: Number of posts per subreddit
            max_users_to_enrich: Maximum number of users to enrich with history
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info("=" * 80)
        logger.info("STARTING DATA PROCESSING PIPELINE")
        logger.info("=" * 80)

        # Step 1: Collect posts
        logger.info(f"\n[STEP 1/5] Collecting posts from {len(subreddits)} subreddits...")
        all_posts = self.scraper.collect_from_multiple_subreddits(
            subreddits=subreddits,
            posts_per_subreddit=posts_per_subreddit
        )
        logger.info(f"✓ Collected {len(all_posts)} posts")

        # Save raw posts
        posts_file = Path(f"data/raw/posts_{timestamp}.json")
        with open(posts_file, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved raw posts to {posts_file}")

        # Step 2: Score posts
        logger.info(f"\n[STEP 2/5] Scoring {len(all_posts)} posts for hate speech and violence...")
        scored_posts = self.scorer.score_multiple_posts(all_posts)

        # Filter high-risk posts
        high_risk_posts = [p for p in scored_posts
                          if p['risk_assessment']['risk_score'] >= 50]
        logger.info(f"✓ Scored all posts. Found {len(high_risk_posts)} high-risk posts")

        # Save scored posts
        scored_posts_file = Path(f"data/processed/posts_scored_{timestamp}.json")
        with open(scored_posts_file, 'w', encoding='utf-8') as f:
            json.dump(scored_posts, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved scored posts to {scored_posts_file}")

        # Step 3: Extract authors and enrich
        logger.info(f"\n[STEP 3/5] Extracting unique authors...")
        unique_authors = set(post['author'] for post in all_posts
                           if post['author'] not in ['[deleted]', 'AutoModerator', '[removed]'])
        logger.info(f"✓ Found {len(unique_authors)} unique authors")

        # Prioritize authors from high-risk posts
        high_risk_authors = set(p['author'] for p in high_risk_posts
                              if p['author'] not in ['[deleted]', 'AutoModerator', '[removed]'])

        # Select users to enrich (prioritize high-risk authors)
        users_to_enrich = list(high_risk_authors)[:max_users_to_enrich]
        remaining_slots = max_users_to_enrich - len(users_to_enrich)

        if remaining_slots > 0:
            other_authors = [u for u in unique_authors if u not in high_risk_authors]
            users_to_enrich.extend(other_authors[:remaining_slots])

        logger.info(f"✓ Selected {len(users_to_enrich)} users for enrichment "
                   f"({len(high_risk_authors)} high-risk priority)")

        # Step 4: Enrich user data
        logger.info(f"\n[STEP 4/5] Enriching user data (fetching 2+ months history)...")
        raw_user_data = []

        for i, username in enumerate(users_to_enrich, 1):
            logger.info(f"  Processing user {i}/{len(users_to_enrich)}: u/{username}")
            user_history = self.scraper.get_user_history(username, limit=100)
            raw_user_data.append(user_history)

        # Save raw user data
        raw_users_file = Path(f"data/raw/users_{timestamp}.json")
        with open(raw_users_file, 'w', encoding='utf-8') as f:
            json.dump(raw_user_data, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved raw user data to {raw_users_file}")

        # Enrich user data with metrics
        enriched_users = self.enricher.enrich_multiple_users(raw_user_data)
        logger.info(f"✓ Enriched {len(enriched_users)} user profiles")

        # Step 5: Score users
        logger.info(f"\n[STEP 5/5] Scoring {len(enriched_users)} users...")
        scored_users = self.scorer.score_multiple_users(enriched_users)

        # Sort by risk score
        scored_users.sort(key=lambda u: u['risk_assessment']['overall_risk_score'],
                         reverse=True)

        # Count risk levels
        risk_distribution = {
            'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'minimal': 0
        }
        for user in scored_users:
            risk_level = user['risk_assessment']['risk_level']
            risk_distribution[risk_level] = risk_distribution.get(risk_level, 0) + 1

        logger.info(f"✓ User risk distribution: {risk_distribution}")

        # Save scored users
        scored_users_file = Path(f"data/processed/users_scored_{timestamp}.json")
        with open(scored_users_file, 'w', encoding='utf-8') as f:
            json.dump(scored_users, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved scored users to {scored_users_file}")

        # Generate summary report
        self._generate_summary_report(
            timestamp, all_posts, scored_posts, high_risk_posts,
            scored_users, risk_distribution, posts_file, scored_posts_file,
            raw_users_file, scored_users_file
        )

        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        # Send data to API
        logger.info("\n" + "=" * 80)
        logger.info("[API EXPORT] Sending data to API...")
        logger.info("=" * 80)
        self._send_to_api(scored_posts, scored_users, posts_file, scored_posts_file,
                          raw_users_file, scored_users_file)

        return {
            'posts': scored_posts,
            'users': scored_users,
            'files': {
                'raw_posts': str(posts_file),
                'scored_posts': str(scored_posts_file),
                'raw_users': str(raw_users_file),
                'scored_users': str(scored_users_file),
            }
        }

    def _send_to_api(self, scored_posts, scored_users, posts_file, scored_posts_file,
                      raw_users_file, scored_users_file):
        """Send scored data to the API"""
        try:
            # Check if API is available
            if not self.api_client.health_check():
                logger.warning("API health check failed. Data not sent to API.")
                return

            logger.info("API connection verified")

            # Send posts
            logger.info(f"Sending {len(scored_posts)} posts to API...")
            posts_result = self.api_client.send_posts(scored_posts)
            logger.info(f"Posts: {posts_result.created} created, "
                        f"{posts_result.skipped} skipped, {posts_result.errors} errors")

            # Send users
            logger.info(f"Sending {len(scored_users)} users to API...")
            users_result = self.api_client.send_users(scored_users)
            logger.info(f"Users: {users_result.created} created, "
                        f"{users_result.skipped} skipped, {users_result.errors} errors")

            logger.info("=" * 80)
            logger.info("API EXPORT COMPLETED!")
            logger.info("=" * 80)

            # Delete JSON files after successful API send
            logger.info("Cleaning up JSON files...")
            try:
                # Delete processed files
                if os.path.exists(scored_posts_file):
                    os.remove(scored_posts_file)
                    logger.debug(f"Deleted {os.path.basename(str(scored_posts_file))}")

                if os.path.exists(scored_users_file):
                    os.remove(scored_users_file)
                    logger.debug(f"Deleted {os.path.basename(str(scored_users_file))}")

                # Also delete corresponding raw files
                if os.path.exists(posts_file):
                    os.remove(posts_file)
                    logger.debug(f"Deleted {os.path.basename(str(posts_file))}")

                if os.path.exists(raw_users_file):
                    os.remove(raw_users_file)
                    logger.debug(f"Deleted {os.path.basename(str(raw_users_file))}")

                # Delete summary report
                summary_file = str(scored_posts_file).replace('posts_scored_', 'summary_report_')
                if os.path.exists(summary_file):
                    os.remove(summary_file)
                    logger.debug(f"Deleted {os.path.basename(summary_file)}")

                logger.info("Cleanup complete - data sent to API")

            except Exception as cleanup_error:
                logger.warning(f"Failed to delete some JSON files: {cleanup_error}")

        except Exception as e:
            logger.error(f"API export failed: {e}. Data is still saved in JSON files.", exc_info=True)

    def _generate_summary_report(self, timestamp, all_posts, scored_posts, high_risk_posts,
                                scored_users, risk_distribution, posts_file, scored_posts_file,
                                raw_users_file, scored_users_file):
        """Generate a summary report"""

        report = {
            'pipeline_run': {
                'timestamp': timestamp,
                'completion_time': datetime.now().isoformat(),
            },
            'posts_analysis': {
                'total_posts_collected': len(all_posts),
                'posts_scored': len(scored_posts),
                'high_risk_posts': len(high_risk_posts),
                'high_risk_percentage': round(len(high_risk_posts) / len(all_posts) * 100, 2) if all_posts else 0,
            },
            'users_analysis': {
                'total_users_analyzed': len(scored_users),
                'risk_distribution': risk_distribution,
                'critical_users': risk_distribution.get('critical', 0),
                'high_risk_users': risk_distribution.get('high', 0),
            },
            'output_files': {
                'raw_posts': str(posts_file),
                'scored_posts': str(scored_posts_file),
                'raw_users': str(raw_users_file),
                'scored_users': str(scored_users_file),
            },
            'top_risk_users': [
                {
                    'username': user['username'],
                    'risk_score': user['risk_assessment']['overall_risk_score'],
                    'risk_level': user['risk_assessment']['risk_level'],
                    'explanation': user['risk_assessment']['explanation'][:200] + '...',
                }
                for user in scored_users[:10]
            ]
        }

        # Save summary report
        report_file = Path(f"data/processed/summary_report_{timestamp}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"\n✓ Generated summary report: {report_file}")

        # Print summary to console
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY REPORT")
        logger.info("=" * 80)
        logger.info(f"\nPosts Analysis:")
        logger.info(f"  • Total posts collected: {report['posts_analysis']['total_posts_collected']}")
        logger.info(f"  • High-risk posts: {report['posts_analysis']['high_risk_posts']} "
                   f"({report['posts_analysis']['high_risk_percentage']}%)")

        logger.info(f"\nUsers Analysis:")
        logger.info(f"  • Total users analyzed: {report['users_analysis']['total_users_analyzed']}")
        logger.info(f"  • Critical risk: {report['users_analysis']['critical_users']}")
        logger.info(f"  • High risk: {report['users_analysis']['high_risk_users']}")
        logger.info(f"  • Risk distribution: {risk_distribution}")

        if scored_users:
            logger.info(f"\nTop 5 Highest Risk Users:")
            for i, user in enumerate(scored_users[:5], 1):
                risk = user['risk_assessment']
                logger.info(f"  {i}. u/{user['username']}: {risk['overall_risk_score']:.1f}/100 "
                           f"({risk['risk_level'].upper()})")

        logger.info(f"\nOutput Files:")
        logger.info(f"  • {posts_file}")
        logger.info(f"  • {scored_posts_file}")
        logger.info(f"  • {raw_users_file}")
        logger.info(f"  • {scored_users_file}")
        logger.info(f"  • {report_file}")

