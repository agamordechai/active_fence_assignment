"""Risk scoring module for hate speech and violent content detection"""
import logging
import re
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class HateSpeechScorer:
    """
    Rule-based hate speech and violence scorer

    This is a simplified rule-based approach. In production, this would use
    ML models like BERT, RoBERTa, or specialized hate speech detection models.

    Keywords are loaded from HurtLex database - a multilingual lexicon of
    offensive, aggressive, and hateful words.
    Source: https://github.com/valeriobasile/hurtlex
    """

    def __init__(self, lexicon_path: str = None):
        """
        Initialize the scorer with HurtLex-based lexicon

        Args:
            lexicon_path: Optional path to custom lexicon file.
                         If None, uses HurtLex-based lexicon from data directory.
        """
        # Load lexicon from HurtLex-based database
        if lexicon_path is None:
            # Use HurtLex-based lexicon path - look in the mounted data directory
            lexicon_path = Path("/app/data/hurtlex_processed.json")
            if not lexicon_path.exists():
                # Fallback to local data directory
                base_dir = Path(__file__).parent.parent.parent.parent
                lexicon_path = base_dir / "data" / "hurtlex_processed.json"

        with open(lexicon_path, 'r', encoding='utf-8') as f:
            lexicon = json.load(f)

        self.hate_keywords = lexicon.get('hate_keywords', {})
        self.violence_keywords = lexicon.get('violence_keywords', {})
        self.slur_patterns = lexicon.get('slur_patterns', [])
        self.context_indicators = lexicon.get('context_indicators', {})

        logger.info(f"Loaded HurtLex-based lexicon from {lexicon_path}")
        logger.info(f"  - Hate keywords: {sum(len(v) for v in self.hate_keywords.values())} total")
        logger.info(f"  - Violence keywords: {sum(len(v) for v in self.violence_keywords.values())} total")
        logger.info(f"  - Slur patterns: {len(self.slur_patterns)}")
        logger.info(f"  - Source: {lexicon.get('source', 'Unknown')}")


    def score_text(self, text: str) -> Dict:
        """
        Score a single text for hate speech and violence

        Args:
            text: Text content to analyze

        Returns:
            Dictionary with risk scores and explanation
        """
        if not text or not isinstance(text, str):
            return {
                'risk_score': 0,
                'risk_level': 'none',
                'hate_score': 0,
                'violence_score': 0,
                'explanation': 'No content to analyze',
                'flags': []
            }

        text_lower = text.lower()
        flags = []
        hate_score = 0
        violence_score = 0

        # Check for hate keywords
        for severity, keywords in self.hate_keywords.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    if severity == 'extreme':
                        hate_score += 30
                        flags.append(f"Extreme hate keyword: '{keyword}'")
                    elif severity == 'high':
                        hate_score += 20
                        flags.append(f"High hate keyword: '{keyword}'")
                    elif severity == 'medium':
                        hate_score += 10
                        flags.append(f"Medium hate keyword: '{keyword}'")

        # Check for violence keywords
        for severity, keywords in self.violence_keywords.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    if severity == 'extreme':
                        violence_score += 30
                        flags.append(f"Extreme violence keyword: '{keyword}'")
                    elif severity == 'high':
                        violence_score += 20
                        flags.append(f"High violence keyword: '{keyword}'")
                    elif severity == 'medium':
                        violence_score += 10
                        flags.append(f"Medium violence keyword: '{keyword}'")

        # Check for slur patterns
        for pattern in self.slur_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                hate_score += 40
                flags.append("Slur or derogatory term detected")

        # Check for multiple exclamation/caps (aggressive tone)
        if re.search(r'[!]{3,}', text):
            hate_score += 5
            flags.append("Aggressive tone (excessive exclamation)")

        if sum(1 for c in text if c.isupper()) / max(len(text), 1) > 0.5 and len(text) > 20:
            hate_score += 5
            flags.append("Aggressive tone (excessive caps)")

        # Check for context indicators (reduce score if present)
        has_discussion_context = any(word in text_lower for word in self.context_indicators['discussion'])
        has_quotation_context = any(word in text_lower for word in self.context_indicators['quotation'])
        has_negation = any(word in text_lower for word in self.context_indicators['negation'])

        context_reduction = 0
        if has_discussion_context:
            context_reduction += 0.2
            flags.append("Discussion context detected")
        if has_quotation_context:
            context_reduction += 0.2
            flags.append("Quotation context detected")
        if has_negation:
            context_reduction += 0.1
            flags.append("Negation detected")

        # Apply context reduction
        hate_score = max(0, hate_score * (1 - context_reduction))
        violence_score = max(0, violence_score * (1 - context_reduction))

        # Calculate overall risk score (0-100)
        risk_score = min(100, hate_score + violence_score)

        # Determine risk level
        risk_level = self._get_risk_level(risk_score)

        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'hate_score': round(hate_score, 2),
            'violence_score': round(violence_score, 2),
            'explanation': self._generate_explanation(risk_score, flags),
            'flags': flags,
        }

    def score_post(self, post: Dict) -> Dict:
        """
        Score a Reddit post

        Args:
            post: Post dictionary with title and selftext

        Returns:
            Post with added risk scoring
        """
        # Combine title and body for scoring
        text_parts = []
        if post.get('title'):
            text_parts.append(post['title'])
        if post.get('selftext'):
            text_parts.append(post['selftext'])

        combined_text = ' '.join(text_parts)

        risk_data = self.score_text(combined_text)

        scored_post = post.copy()
        scored_post['risk_assessment'] = risk_data
        scored_post['scored_at'] = datetime.now().isoformat()

        return scored_post

    def score_user(self, user_data: Dict) -> Dict:
        """
        Score a user based on their content history

        Args:
            user_data: Enriched user data with posts and comments

        Returns:
            User data with risk scoring
        """
        username = user_data.get('username', 'unknown')
        all_text = user_data.get('content', {}).get('all_text', [])

        if not all_text:
            return {
                **user_data,
                'risk_assessment': {
                    'overall_risk_score': 0,
                    'risk_level': 'none',
                    'average_hate_score': 0,
                    'average_violence_score': 0,
                    'high_risk_content_count': 0,
                    'explanation': 'No content available for scoring',
                    'content_scores': []
                }
            }

        # Score each piece of content
        content_scores = []
        total_hate = 0
        total_violence = 0
        high_risk_count = 0

        for text in all_text:
            score = self.score_text(text)
            content_scores.append(score)
            total_hate += score['hate_score']
            total_violence += score['violence_score']

            if score['risk_score'] >= 50:  # High risk threshold
                high_risk_count += 1

        # Calculate averages
        avg_hate = total_hate / len(content_scores)
        avg_violence = total_violence / len(content_scores)

        # Calculate overall user risk score
        # Weight: average score (70%) + high risk content frequency (30%)
        avg_risk = (avg_hate + avg_violence)
        high_risk_multiplier = 1 + (high_risk_count / len(content_scores))
        overall_risk = min(100.0, avg_risk * 0.7 * high_risk_multiplier)

        risk_level = self._get_risk_level(overall_risk)

        # Generate explanation
        explanation = self._generate_user_explanation(
            username, overall_risk, high_risk_count, len(content_scores), avg_hate, avg_violence
        )

        scored_user = user_data.copy()
        scored_user['risk_assessment'] = {
            'overall_risk_score': round(overall_risk, 2),
            'risk_level': risk_level,
            'average_hate_score': round(avg_hate, 2),
            'average_violence_score': round(avg_violence, 2),
            'high_risk_content_count': high_risk_count,
            'total_content_analyzed': len(content_scores),
            'explanation': explanation,
            'scored_at': datetime.now().isoformat(),
        }

        logger.info(f"Scored u/{username}: Risk={overall_risk:.2f} ({risk_level}), "
                   f"High-risk items={high_risk_count}/{len(content_scores)}")

        return scored_user

    def _get_risk_level(self, score: float) -> str:
        """Convert numeric score to risk level"""
        if score >= 70:
            return 'critical'
        elif score >= 50:
            return 'high'
        elif score >= 30:
            return 'medium'
        elif score >= 10:
            return 'low'
        else:
            return 'minimal'

    def _generate_explanation(self, risk_score: float, flags: List[str]) -> str:
        """Generate human-readable explanation"""
        if risk_score == 0:
            return "No concerning content detected."

        risk_level = self._get_risk_level(risk_score)
        explanation = f"Risk Level: {risk_level.upper()} ({risk_score:.0f}/100). "

        if flags:
            explanation += f"Detected: {', '.join(flags[:5])}"
            if len(flags) > 5:
                explanation += f" and {len(flags) - 5} more indicators."

        return explanation

    def _generate_user_explanation(self, username: str, overall_risk: float,
                                   high_risk_count: int, total_items: int,
                                   avg_hate: float, avg_violence: float) -> str:
        """Generate explanation for user risk score"""
        risk_level = self._get_risk_level(overall_risk)

        explanation = f"User u/{username} has a {risk_level.upper()} risk level ({overall_risk:.1f}/100). "
        explanation += f"Analysis of {total_items} content items revealed "
        explanation += f"{high_risk_count} high-risk posts/comments. "
        explanation += f"Average hate speech indicators: {avg_hate:.1f}, "
        explanation += f"Average violence indicators: {avg_violence:.1f}."

        if overall_risk >= 70:
            explanation += " IMMEDIATE REVIEW RECOMMENDED."
        elif overall_risk >= 50:
            explanation += " Should be monitored closely."
        elif overall_risk >= 30:
            explanation += " Moderate concern, periodic monitoring advised."

        return explanation

    def score_multiple_posts(self, posts: List[Dict]) -> List[Dict]:
        """Score multiple posts"""
        return [self.score_post(post) for post in posts]

    def score_multiple_users(self, users: List[Dict]) -> List[Dict]:
        """Score multiple users"""
        return [self.score_user(user) for user in users]