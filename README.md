# Daily News Digest

A system for automatically collecting, summarizing, and emailing news articles.

## Overview

This system fetches news articles from multiple sources, uses AI to summarize them, and sends the digest via email. It's designed to focus on news that's most relevant to the user's interests.

## Features

- **Two-Phase News Fetching**: Efficiently fetches news by first collecting headlines and descriptions, then using AI to select which articles to scrape in full detail
- **AI-Powered Summarization**: Uses GPT-4o to create a personalized digest of the news
- **Multiple News Sources**: Scrapes from various sources including TechCrunch and CNN
- **Category Filtering**: Organizes news by categories like AI, technology, etc.
- **Customizable Prompts**: Allows customization of the AI summarization prompt
- **Email Delivery**: Sends formatted HTML emails using SendGrid

## How It Works

1. **Phase 1 - Initial Scraping**:

   - Fetches headlines, URLs, and short descriptions from news sources
   - Does not download full article content yet

2. **Phase 2 - AI Selection**:

   - Uses OpenAI to analyze the headlines and descriptions
   - Selects the most relevant articles based on user interests (AI, tech innovations, etc.)

3. **Phase 3 - Detailed Scraping**:

   - Fetches full content only for the selected articles
   - Saves bandwidth and processing time by only scraping what's needed

4. **Summarization**:

   - Sends the selected articles to GPT-4o for summarization
   - Creates a personalized digest highlighting the most important information

5. **Email Delivery**:
   - Formats the summary as HTML email
   - Sends to specified recipients via SendGrid

## Usage

### Basic Run

```bash
python -m __main__ --test
```

### Custom Run

```bash
python -m __main__ --test --categories ai,technology --emails someone@example.com
```

### Test Workflow

To test the two-phase news fetching workflow:

```bash
python test_workflow.py
```

## Configuration

Key settings can be configured through environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key for summarization
- `SENDGRID_API_KEY`: SendGrid API key for sending emails
