"""Complete data processing pipeline: collect -> enrich -> score"""
import logging

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


    def run_full_pipeline(self, subreddits: list, posts_per_subreddit: int = 25,
                         max_users_to_enrich: int = 20,
                         search_terms: list = None, posts_per_search: int = 25):
        """
        Run complete pipeline: collection -> enrichment -> scoring

        Args:
            subreddits: List of subreddit names to collect from
            posts_per_subreddit: Number of posts per subreddit
            max_users_to_enrich: Maximum number of users to enrich with history
            search_terms: List of search terms for finding controversial content
            posts_per_search: Number of posts to fetch per search term
        """
        logger.info("=" * 80)
        logger.info("STARTING DATA PROCESSING PIPELINE")
        logger.info("=" * 80)

        # Step 1a: Collect posts from subreddits
        logger.info(f"\n[STEP 1/5] Collecting posts from {len(subreddits)} subreddits...")
        all_posts = self.scraper.collect_from_multiple_subreddits(
            subreddits=subreddits,
            posts_per_subreddit=posts_per_subreddit
        )
        logger.info(f"Collected {len(all_posts)} posts from subreddits")

        # Step 1b: Collect posts using search terms
        if search_terms:
            logger.info(f"\n[STEP 1b/5] Searching for posts with {len(search_terms)} search terms...")
            seen_ids = {p['id'] for p in all_posts}
            for term in search_terms:
                search_results = self.scraper.search_posts(query=term, limit=posts_per_search)
                # Deduplicate - only add posts we haven't seen
                new_posts = [p for p in search_results if p['id'] not in seen_ids]
                for p in new_posts:
                    seen_ids.add(p['id'])
                all_posts.extend(new_posts)
                logger.info(f"  Search '{term}': found {len(search_results)} posts, {len(new_posts)} new")
            logger.info(f"Total posts after search: {len(all_posts)}")

        # Step 2: Score posts
        logger.info(f"\n[STEP 2/5] Scoring {len(all_posts)} posts for hate speech and violence...")
        scored_posts = self.scorer.score_multiple_posts(all_posts)

        # Filter to keep only posts with controversial, harmful, or violent content (risk_score > 0)
        scored_posts = [p for p in scored_posts
                        if p['risk_assessment']['risk_score'] > 0]
        logger.info(f"Filtered to {len(scored_posts)} posts with harmful/violent content")

        # Filter high-risk posts
        high_risk_posts = [p for p in scored_posts
                          if p['risk_assessment']['risk_score'] >= 50]
        logger.info(f"Found {len(high_risk_posts)} high-risk posts")


        # Step 3: Extract authors from harmful posts only
        logger.info(f"\n[STEP 3/5] Extracting authors from harmful content posts...")
        # Only consider authors from posts with harmful content (scored_posts already filtered)
        unique_authors = set(post['author'] for post in scored_posts
                           if post['author'] not in ['[deleted]', 'AutoModerator', '[removed]'])
        logger.info(f"Found {len(unique_authors)} unique authors from harmful content")

        # Prioritize authors from high-risk posts
        high_risk_authors = set(p['author'] for p in high_risk_posts
                              if p['author'] not in ['[deleted]', 'AutoModerator', '[removed]'])

        # Select users to enrich (prioritize high-risk authors)
        users_to_enrich = list(high_risk_authors)[:max_users_to_enrich]
        remaining_slots = max_users_to_enrich - len(users_to_enrich)

        if remaining_slots > 0:
            other_authors = [u for u in unique_authors if u not in high_risk_authors]
            users_to_enrich.extend(other_authors[:remaining_slots])

        logger.info(f"Selected {len(users_to_enrich)} users for enrichment "
                   f"({len(high_risk_authors)} high-risk priority)")

        # Step 4: Enrich user data
        logger.info(f"\n[STEP 4/5] Enriching user data (fetching 2+ months history)...")
        raw_user_data = []
        skipped_users = 0

        for i, username in enumerate(users_to_enrich, 1):
            logger.info(f"  Processing user {i}/{len(users_to_enrich)}: u/{username}")
            user_history = self.scraper.get_user_history(username, limit=100)

            # Skip users with no content (new users, private profiles, deleted accounts)
            if user_history['total_posts'] == 0 and user_history['total_comments'] == 0:
                logger.warning(f"  Skipping u/{username}: no posts or comments (new user, private, or deleted)")
                skipped_users += 1
                continue

            raw_user_data.append(user_history)

        logger.info(f"Fetched data for {len(raw_user_data)} users, skipped {skipped_users} users with no content")

        # Enrich user data with metrics
        enriched_users = self.enricher.enrich_multiple_users(raw_user_data)
        logger.info(f"Enriched {len(enriched_users)} user profiles")

        # Step 5: Score users
        logger.info(f"\n[STEP 5/5] Scoring {len(enriched_users)} users...")
        scored_users = self.scorer.score_multiple_users(enriched_users)

        # Filter to keep only users with harmful/violent content (overall_risk_score > 0)
        scored_users = [u for u in scored_users
                        if u['risk_assessment']['overall_risk_score'] > 0]
        logger.info(f"Filtered to {len(scored_users)} users with harmful/violent content")

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

        logger.info(f"User risk distribution: {risk_distribution}")

        # Generate summary report (in memory only)
        self._log_summary_report(all_posts, scored_posts, high_risk_posts,
                                scored_users, risk_distribution)

        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)

        # Send data to API
        logger.info("\n" + "=" * 80)
        logger.info("[API EXPORT] Sending data to API...")
        logger.info("=" * 80)
        self._send_to_api(scored_posts, scored_users)

        return {
            'posts': scored_posts,
            'users': scored_users,
        }

    def _send_to_api(self, scored_posts, scored_users):
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

        except Exception as e:
            logger.error(f"API export failed: {e}", exc_info=True)

    def _log_summary_report(self, all_posts, scored_posts, high_risk_posts,
                           scored_users, risk_distribution):
        """Log summary report to console"""
        high_risk_percentage = round(len(high_risk_posts) / len(all_posts) * 100, 2) if all_posts else 0

        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY REPORT")
        logger.info("=" * 80)
        logger.info(f"\nPosts Analysis:")
        logger.info(f"  Total posts collected: {len(all_posts)}")
        logger.info(f"  High-risk posts: {len(high_risk_posts)} ({high_risk_percentage}%)")

        logger.info(f"\nUsers Analysis:")
        logger.info(f"  Total users analyzed: {len(scored_users)}")
        logger.info(f"  Critical risk: {risk_distribution.get('critical', 0)}")
        logger.info(f"  High risk: {risk_distribution.get('high', 0)}")
        logger.info(f"  Risk distribution: {risk_distribution}")

        if scored_users:
            logger.info(f"\nTop 5 Highest Risk Users:")
            for i, user in enumerate(scored_users[:5], 1):
                risk = user['risk_assessment']
                logger.info(f"  {i}. u/{user['username']}: {risk['overall_risk_score']:.1f}/100 "
                           f"({risk['risk_level'].upper()})")