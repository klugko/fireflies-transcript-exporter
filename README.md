# Fireflies Transcript Downloader

A command-line tool to download meeting transcripts from [Fireflies.ai](https://fireflies.ai) using their GraphQL API.

## Features

- Download full meeting transcripts with speaker identification and timestamps
- Export to JSON (raw data) or formatted text
- Extract meeting summaries, keywords, and action items
- Support for both transcript IDs and Fireflies URLs

## Prerequisites

- Python 3.8+
- A Fireflies.ai account with API access
- Your Fireflies API key ([Get it here](https://app.fireflies.ai/integrations/custom/fireflies))

## Installation

1. Clone the repository:

```bash
git clone https://github.com/klugko/fireflies-transcript-exporter.git
cd fireflies-transcript-exporter
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure your API key:

```bash
cp .env.example .env
```

Edit `.env` and add your Fireflies API key:

```
FIREFLIES_API_KEY=your_api_key_here
```

## Usage

### Basic Usage

Download a transcript using its ID:

```bash
python download_transcript.py your_transcript_id
```

Or using a Fireflies URL:

```bash
python download_transcript.py https://app.fireflies.ai/view/your_transcript_id
```

### Options

```
usage: download_transcript.py [-h] [-o OUTPUT] [-f {txt,json,both}] transcript

Download transcripts from Fireflies.ai

positional arguments:
  transcript            Transcript ID or Fireflies URL

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory (default: current directory)
  -f {txt,json,both}, --format {txt,json,both}
                        Output format (default: both)
```

### Examples

Download only the JSON file:

```bash
python download_transcript.py -f json your_transcript_id
```

Download to a specific directory:

```bash
python download_transcript.py -o ./transcripts your_transcript_id
```

## Output Format

### Text File (.txt)

The formatted text file includes:

- Meeting metadata (title, date, duration, participants)
- Summary and keywords
- Action items
- Full transcript with timestamps and speaker names

Example:

```
================================================================================
TITLE: Weekly Team Standup
ID: 01KHJNY4DDYNKW4ECNE2B2NSKQ
DURATION: 45m 30s
DATE: 2024-01-15 10:00:00
PARTICIPANTS: alice@example.com, bob@example.com
================================================================================

--- SUMMARY ---
Discussion about Q1 roadmap and sprint planning...

--- ACTION ITEMS ---
  - Review PR #123
  - Update documentation

================================================================================
FULL TRANSCRIPT
================================================================================

--- Alice ---
[00:00] Good morning everyone, let's get started.
[00:05] First, I'd like to discuss the roadmap.

--- Bob ---
[00:15] Sure, I have some updates on the backend work.
```

### JSON File (.json)

The JSON file contains the raw API response with complete data structure, useful for further processing or integration with other tools.

## API Reference

This tool uses the [Fireflies GraphQL API](https://docs.fireflies.ai/graphql-api/query/transcript). The following data is retrieved:

| Field | Description |
|-------|-------------|
| `title` | Meeting title |
| `id` | Unique transcript identifier |
| `duration` | Meeting duration in seconds |
| `date` | Meeting timestamp |
| `participants` | List of participant emails |
| `sentences` | Array of transcript sentences with speaker and timing |
| `summary` | AI-generated summary, keywords, and action items |

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.
