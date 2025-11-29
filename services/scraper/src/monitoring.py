"""User monitoring module for daily scanning of flagged users"""
import logging
from datetime import datetime
from typing import List, Dict, Any

from src.collectors.reddit_scraper import RedditScraper
from src.enrichers.user_enricher import UserEnricher
from src.scorers.hate_speech_scorer import HateSpeechScorer
from src.api_client import APIClient

logger = logging.getLogger(__name__)


class UserMonitor:
    """
    Monitors flagged users for new high-risk content.
    Designed to run daily to check for new posts/comments from users
    who have been flagged as high-risk.
    """

    def __init__(self, high_risk_threshold: int = 50, critical_risk_threshold: int = 70):
        self.scraper = RedditScraper(rate_limit_delay=2.0)
        self.enricher = UserEnricher()
        self.scorer = HateSpeechScorer()
        self.api_client = APIClient()
        self.high_risk_threshold = high_risk_threshold
        self.critical_risk_threshold = critical_risk_threshold

    def get_monitored_users(self) -> List[Dict]:
        """Fetch list of users marked for monitoring from API"""
        try:
            return self.api_client.get_monitored_users()
        except Exception as e:
            logger.error(f"Failed to fetch monitored users: {e}")
            return []

    def scan_user(self, username: str) -> Dict[str, Any]:
        """
        Scan a single user for new content and assess risk.

        Returns:
            Dictionary with scan results including any alerts generated
        """
        logger.info(f"Scanning monitored user: u/{username}")

        result = {
            'username': username,
            'scanned_at': datetime.now().isoformat(),
            'new_posts_count': 0,
            'new_comments_count': 0,
            'high_risk_items': [],
            'alerts_generated': [],
            'max_risk_score': 0,
            'status': 'success'
        }

        try:
            # Fetch recent user activity
            user_history = self.scraper.get_user_history(username, limit=50)

            if user_history['total_posts'] == 0 and user_history['total_comments'] == 0:
                logger.warning(f"  u/{username}: No content found (private/deleted/suspended)")
                result['status'] = 'no_content'
                return result

            result['new_posts_count'] = user_history['total_posts']
            result['new_comments_count'] = user_history['total_comments']

            # Enrich and score user content
            enriched = self.enricher.enrich_user_data(user_history)
            scored = self.scorer.score_user(enriched)

            risk_assessment = scored.get('risk_assessment', {})
            overall_risk = risk_assessment.get('overall_risk_score', 0)
            result['max_risk_score'] = overall_risk

            # Check for high-risk content in individual items
            all_text = enriched.get('content', {}).get('all_text', [])
            for text in all_text:
                score_result = self.scorer.score_text(text)
                if score_result['risk_score'] >= self.high_risk_threshold:
                    result['high_risk_items'].append({
                        'text_preview': text[:200] + '...' if len(text) > 200 else text,
                        'risk_score': score_result['risk_score'],
                        'risk_level': score_result['risk_level'],
                        'flags': score_result['flags']
                    })

            # Generate alerts for high-risk content
            if result['high_risk_items']:
                for item in result['high_risk_items']:
                    alert = self._create_alert(username, item)
                    result['alerts_generated'].append(alert)

            # Log monitoring activity
            self._log_monitoring_activity(username, result)

            logger.info(f"  u/{username}: Scanned {result['new_posts_count']} posts, "
                       f"{result['new_comments_count']} comments, "
                       f"{len(result['high_risk_items'])} high-risk items found")

        except Exception as e:
            logger.error(f"Error scanning u/{username}: {e}")
            result['status'] = 'error'
            result['error'] = str(e)

        return result

    def _create_alert(self, username: str, high_risk_item: Dict) -> Dict:
        """Create an alert for high-risk content"""
        severity = 'critical' if high_risk_item['risk_score'] >= self.critical_risk_threshold else 'high'

        alert = {
            'username': username,
            'alert_type': 'monitored_user_content',
            'severity': severity,
            'risk_score': high_risk_item['risk_score'],
            'description': f"High-risk content detected from monitored user u/{username}",
            'details': {
                'text_preview': high_risk_item['text_preview'],
                'risk_level': high_risk_item['risk_level'],
                'flags': high_risk_item['flags'],
                'detected_at': datetime.now().isoformat()
            },
            'status': 'new'
        }

        # Send alert to API
        try:
            self.api_client.create_alert(alert)
            logger.warning(f"  ALERT [{severity.upper()}]: u/{username} - Risk score: {high_risk_item['risk_score']}")
        except Exception as e:
            logger.error(f"Failed to create alert for u/{username}: {e}")

        return alert

    def _log_monitoring_activity(self, username: str, result: Dict) -> None:
        """Log monitoring activity to API"""
        log_entry = {
            'username': username,
            'activity_type': 'daily_scan',
            'description': f"Daily monitoring scan for u/{username}",
            'findings': {
                'posts_scanned': result['new_posts_count'],
                'comments_scanned': result['new_comments_count'],
                'high_risk_items': len(result['high_risk_items']),
                'alerts_generated': len(result['alerts_generated']),
                'max_risk_score': result['max_risk_score'],
                'status': result['status']
            }
        }

        try:
            self.api_client.create_monitoring_log(log_entry)
        except Exception as e:
            logger.error(f"Failed to log monitoring activity for u/{username}: {e}")

    def run_daily_monitoring(self) -> Dict[str, Any]:
        """
        Run daily monitoring scan for all flagged users.

        Returns:
            Summary of monitoring run with statistics
        """
        logger.info("=" * 80)
        logger.info("STARTING DAILY USER MONITORING")
        logger.info("=" * 80)

        start_time = datetime.now()

        # Get list of monitored users
        monitored_users = self.get_monitored_users()

        if not monitored_users:
            logger.info("No users currently flagged for monitoring")
            return {
                'status': 'completed',
                'users_scanned': 0,
                'total_alerts_generated': 0,
                'message': 'No users to monitor'
            }

        logger.info(f"Found {len(monitored_users)} users to monitor")

        # Scan each monitored user
        results = []
        total_alerts = 0
        high_risk_users = []

        for i, user in enumerate(monitored_users, 1):
            username = user.get('username') if isinstance(user, dict) else user
            logger.info(f"\n[{i}/{len(monitored_users)}] Scanning u/{username}...")

            result = self.scan_user(username)
            results.append(result)

            alerts_count = len(result.get('alerts_generated', []))
            total_alerts += alerts_count

            if result['max_risk_score'] >= self.high_risk_threshold:
                high_risk_users.append({
                    'username': username,
                    'risk_score': result['max_risk_score'],
                    'alerts': alerts_count
                })

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        summary = {
            'status': 'completed',
            'started_at': start_time.isoformat(),
            'completed_at': end_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'users_scanned': len(monitored_users),
            'total_alerts_generated': total_alerts,
            'high_risk_users_found': len(high_risk_users),
            'high_risk_users': high_risk_users
        }

        logger.info("\n" + "=" * 80)
        logger.info("DAILY MONITORING COMPLETED")
        logger.info("=" * 80)
        logger.info(f"  Users scanned: {summary['users_scanned']}")
        logger.info(f"  Alerts generated: {summary['total_alerts_generated']}")
        logger.info(f"  High-risk users found: {summary['high_risk_users_found']}")
        logger.info(f"  Duration: {summary['duration_seconds']}s")
        logger.info("=" * 80)

        return summary
