# Data Automation Analyst - Home Assignment

## Objective

As we seek to identify and analyze the spread of violent hate speech on Reddit, we will define the following business requirements:

Your task is to deliver an automatically collected and scored data feed of Reddit posts, with the following fields: language, date published, post text, risk score.

You are also expected to deliver a prioritized data feed of suspected Reddit user accounts, including the calculated score and an explanation describing why the user was scored as such.

## Task

### Part 1: Technical and Business Specification

- Outline the data collection, enrichment, analysis, and scoring methodologies.

### Part 2: Implementation

#### Data Collection from Reddit
- Focus only on posts or users discussing controversial, harmful, and violent content.
- Use a combination of search terms and subreddit targeting to collect posts and user data
- Collect metadata, including publication date, post content, and author

#### Data Enrichment
- For each identified Reddit user, gather their recent post history - bring at least 2 months of the user's data.

#### Risk Score Development
- Please write out a detailed methodology of how you could build and then implement a risk score to estimate the risk level (in terms of violence or hate) of the post and users in terms of violent language or hate speech.

#### Edge Cases Consideration
- Ensure correct handling of edge cases, such as new users with no posts or comments, and users with private profiles.

#### Monitoring Scale
- Design a system capable of daily monitoring of flagged users' new posts, with alerts for high-risk content

#### Implementation Language
- Please use Python programming language for the solution

## Deliverables

- **Technical and Business Specification Document**: Outline the objectives, methodologies, tools, and expected outcomes of the project. (PDF)
  - High-level description of the technical solution: Provide an overview of the technical approach, including any frameworks, APIs, libraries, or tools used.
- **Technical Implementation Code**: All code that was used for scraping, enrichment, and scoring. (py/ipynb)
- **Raw Data Collection**: Provide raw datasets collected from Reddit and enriched with user post history. Please provide it in JSON or CSV format (the target is around 100 Reddit accounts or posts).
- **Running the code**: Explain how to set up and run your scraping solution, including any dependencies or environment setup required.
- **Test plan and results**: Detail a testing strategy for ensuring the reliability and accuracy of your scraping solution. Include test cases and links to results, if possible.
