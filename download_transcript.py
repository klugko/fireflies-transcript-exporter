#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.fireflies.ai/graphql"

TRANSCRIPT_QUERY = """
query GetTranscriptContent($id: String!) {
  transcript(id: $id) {
    title
    id
    transcript_url
    duration
    date
    participants
    sentences {
      text
      speaker_id
      speaker_name
      start_time
      end_time
    }
    summary {
      keywords
      action_items
      overview
      shorthand_bullet
    }
  }
}
"""


class FirefliesClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key is required")
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def get_transcript(self, transcript_id: str) -> dict:
        payload = {
            "query": TRANSCRIPT_QUERY,
            "variables": {"id": transcript_id}
        }
        response = self.session.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL Error: {data['errors']}")

        return data


class TranscriptFormatter:
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"[{minutes:02d}:{secs:02d}]"

    @staticmethod
    def format_duration(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        if minutes > 0:
            return f"{minutes}m {secs}s"
        return f"{secs}s"

    def format(self, data: dict) -> str:
        transcript = data.get("data", {}).get("transcript")
        if not transcript:
            raise ValueError("Transcript not found in response")

        lines = []
        self._add_header(lines, transcript)
        self._add_summary(lines, transcript.get("summary", {}))
        self._add_sentences(lines, transcript.get("sentences", []))

        return "\n".join(lines)

    def _add_header(self, lines: list, transcript: dict):
        lines.append("=" * 80)
        lines.append(f"TITLE: {transcript.get('title', 'N/A')}")
        lines.append(f"ID: {transcript.get('id', 'N/A')}")

        duration = transcript.get("duration", 0)
        lines.append(f"DURATION: {self.format_duration(duration)}")

        date_ts = transcript.get("date")
        if date_ts:
            date_str = datetime.fromtimestamp(date_ts / 1000).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"DATE: {date_str}")

        participants = transcript.get("participants", [])
        if participants:
            lines.append(f"PARTICIPANTS: {', '.join(participants)}")

        lines.append("=" * 80)
        lines.append("")

    def _add_summary(self, lines: list, summary: dict):
        if not summary:
            return

        if summary.get("overview"):
            lines.append("--- SUMMARY ---")
            lines.append(summary["overview"])
            lines.append("")

        keywords = summary.get("keywords")
        if keywords:
            lines.append("--- KEYWORDS ---")
            if isinstance(keywords, list):
                lines.append(", ".join(keywords))
            else:
                lines.append(str(keywords))
            lines.append("")

        action_items = summary.get("action_items")
        if action_items:
            lines.append("--- ACTION ITEMS ---")
            if isinstance(action_items, str):
                lines.append(action_items.strip())
            else:
                for item in action_items:
                    lines.append(f"  - {item}")
            lines.append("")

    def _add_sentences(self, lines: list, sentences: list):
        if not sentences:
            return

        lines.append("=" * 80)
        lines.append("FULL TRANSCRIPT")
        lines.append("=" * 80)
        lines.append("")

        current_speaker = None
        for sentence in sentences:
            speaker = sentence.get("speaker_name") or sentence.get("speaker_id", "Unknown")
            text = sentence.get("text", "")
            start_time = sentence.get("start_time", 0)

            if speaker != current_speaker:
                lines.append("")
                lines.append(f"--- {speaker} ---")
                current_speaker = speaker

            timestamp = self.format_timestamp(start_time)
            lines.append(f"{timestamp} {text}")


def extract_transcript_id(url_or_id: str) -> str:
    pattern = r"([A-Z0-9]{26})"
    match = re.search(pattern, url_or_id)
    if match:
        return match.group(1)
    return url_or_id


def save_output(content: str, filepath: Path):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Download transcripts from Fireflies.ai",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "transcript",
        help="Transcript ID or Fireflies URL"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory (default: current directory)",
        default="."
    )
    parser.add_argument(
        "-f", "--format",
        choices=["txt", "json", "both"],
        default="both",
        help="Output format (default: both)"
    )
    args = parser.parse_args()

    api_key = os.getenv("FIREFLIES_API_KEY")
    if not api_key:
        print("Error: FIREFLIES_API_KEY environment variable is not set", file=sys.stderr)
        sys.exit(1)

    transcript_id = extract_transcript_id(args.transcript)
    output_dir = Path(args.output)

    print(f"Downloading transcript: {transcript_id}")

    try:
        client = FirefliesClient(api_key)
        data = client.get_transcript(transcript_id)

        transcript_title = data.get("data", {}).get("transcript", {}).get("title", transcript_id)
        safe_title = re.sub(r'[^\w\s-]', '', transcript_title).strip().replace(' ', '_')[:50]
        base_filename = f"{safe_title}_{transcript_id}"

        if args.format in ("json", "both"):
            json_path = output_dir / f"{base_filename}.json"
            save_output(json.dumps(data, ensure_ascii=False, indent=2), json_path)
            print(f"Saved: {json_path}")

        if args.format in ("txt", "both"):
            formatter = TranscriptFormatter()
            formatted = formatter.format(data)
            txt_path = output_dir / f"{base_filename}.txt"
            save_output(formatted, txt_path)
            print(f"Saved: {txt_path}")

        print("Done.")

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
