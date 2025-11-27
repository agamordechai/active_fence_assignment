"""User data enrichment module"""
import logging
from typing import Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class UserEnricher:
    """Enriches user data with additional metadata and analysis"""

    def __init__(self):
        self.two_months_ago = (datetime.now() - timedelta(days=60)).timestamp()

    def enrich_user_data(self, user_data: Dict) -> Dict:
        """
        Enrich user data with calculated metrics

        Args:
            user_data: Raw user data from scraper

        Returns:
            Enriched user data with additional metrics
        """
        username = user_data.get('username', 'unknown')
        posts = user_data.get('posts', [])
        comments = user_data.get('comments', [])

        # Filter to last 2 months
        recent_posts = [p for p in posts if p.get('created_utc', 0) >= self.two_months_ago]
        recent_comments = [c for c in comments if c.get('created_utc', 0) >= self.two_months_ago]

        # Calculate activity metrics
        total_activity = len(recent_posts) + len(recent_comments)

        # Calculate average scores
        avg_post_score = sum(p.get('score', 0) for p in recent_posts) / len(recent_posts) if recent_posts else 0
        avg_comment_score = sum(c.get('score', 0) for c in recent_comments) / len(recent_comments) if recent_comments else 0

        # Get unique subreddits
        subreddits_posted = set(p.get('subreddit', '') for p in recent_posts)
        subreddits_commented = set(c.get('subreddit', '') for c in recent_comments)
        unique_subreddits = subreddits_posted.union(subreddits_commented)

        # Calculate activity frequency (posts/comments per day)
        days_active = 60  # Last 2 months
        activity_per_day = total_activity / days_active if days_active > 0 else 0

        # Collect all text content for later scoring
        all_text = []
        for post in recent_posts:
            if post.get('title'):
                all_text.append(post['title'])
            if post.get('selftext'):
                all_text.append(post['selftext'])

        for comment in recent_comments:
            if comment.get('body'):
                all_text.append(comment['body'])

        enriched_data = {
            'username': username,
            'enrichment_timestamp': datetime.now().isoformat(),
            'activity_metrics': {
                'total_posts': len(posts),
                'total_comments': len(comments),
                'recent_posts_2m': len(recent_posts),
                'recent_comments_2m': len(recent_comments),
                'total_recent_activity': total_activity,
                'activity_per_day': round(activity_per_day, 2),
                'avg_post_score': round(avg_post_score, 2),
                'avg_comment_score': round(avg_comment_score, 2),
            },
            'subreddit_diversity': {
                'unique_subreddits_count': len(unique_subreddits),
                'subreddits': sorted(list(unique_subreddits)),
                'primary_subreddits_posted': sorted(list(subreddits_posted))[:10],
                'primary_subreddits_commented': sorted(list(subreddits_commented))[:10],
            },
            'content': {
                'all_text': all_text,
                'total_text_items': len(all_text),
            },
            'raw_data': {
                'posts': recent_posts,
                'comments': recent_comments,
            },
            'profile_status': self._determine_profile_status(total_activity, posts, comments),
        }

        logger.info(f"Enriched data for u/{username}: {total_activity} recent activities "
                   f"across {len(unique_subreddits)} subreddits")

        return enriched_data

    def _determine_profile_status(self, total_activity: int, posts: List, comments: List) -> str:
        """Determine the status of a user's profile"""
        if total_activity == 0 and (not posts and not comments):
            return "new_user_no_activity"
        elif total_activity == 0 and (posts or comments):
            return "no_recent_activity"
        elif total_activity < 10:
            return "low_activity"
        elif total_activity < 50:
            return "moderate_activity"
        else:
            return "high_activity"

    def enrich_multiple_users(self, users_data: List[Dict]) -> List[Dict]:
        """
        Enrich multiple users' data

        Args:
            users_data: List of raw user data dictionaries

        Returns:
            List of enriched user data dictionaries
        """
        enriched_users = []

        for user_data in users_data:
            try:
                enriched = self.enrich_user_data(user_data)
                enriched_users.append(enriched)
            except Exception as e:
                username = user_data.get('username', 'unknown')
                logger.error(f"Error enriching user u/{username}: {e}")

        return enriched_users

