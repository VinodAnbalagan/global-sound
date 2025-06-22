import pysrt

class SubtitleGenerator:
    """
    Creates .srt subtitle files from segments with start/end times and text.

    """
    def create_srt_file(self, filename_prefix: str, segments: list) -> str:
        """
        Converts segments into a SubRip (.srt) file.

        Args:
            filename_prefix (str): Base name for the output file.
            segments (list): List of {'start', 'end', 'text'} dicts.

        Returns:
            str: Path to the saved subtitle file.
        """
        print(f"Step 4: Generating SRT file: {filename_prefix}.srt...")
        subs = pysrt.SubRipFile()

        for i, seg in enumerate(segments):
            sub_item = pysrt.SubRipItem(
                index=i + 1,
                start=pysrt.SubRipTime.from_seconds(seg['start']),
                end=pysrt.SubRipTime.from_seconds(seg['end']),
                text=seg['text'].strip()
            )
            subs.append(sub_item)

        output_path = f"{filename_prefix}.srt"
        subs.save(output_path, encoding='utf-8')
        print(f"SRT file saved: {output_path}")
        return output_path