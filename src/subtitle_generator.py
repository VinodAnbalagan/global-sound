# src/subtitle_generator.py

import pysrt
import datetime # We need this library

class SubtitleGenerator:
    """
    Creates .srt subtitle files from segments with start/end times and text.
    """
    def _seconds_to_srt_time(self, total_seconds):
        """
        Helper function to convert seconds to a pysrt.SubRipTime object.
        """
        # Create a timedelta object
        td = datetime.timedelta(seconds=total_seconds)
        # Manually calculate hours, minutes, seconds, and milliseconds
        minutes, seconds = divmod(td.seconds, 60)
        hours, minutes = divmod(minutes, 60)
        milliseconds = td.microseconds // 1000
        
        return pysrt.SubRipTime(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)

    def create_srt_file(self, filename_prefix: str, segments: list) -> str:
        """
        Converts segments into a SubRip (.srt) file.
        """
        print(f"Step 4: Generating SRT file: {filename_prefix}.srt...")
        subs = pysrt.SubRipFile()

        for i, seg in enumerate(segments):
            # --- THIS IS THE KEY CHANGE ---
            # Instead of .from_seconds, we will use our new helper function
            start_time = self._seconds_to_srt_time(seg['start'])
            end_time = self._seconds_to_srt_time(seg['end'])
            
            sub_item = pysrt.SubRipItem(
                index=i + 1,
                start=start_time,
                end=end_time,
                text=seg['text'].strip()
            )
            subs.append(sub_item)

        output_path = f"{filename_prefix}.srt"
        subs.save(output_path, encoding='utf-8')
        print(f"SRT file saved: {output_path}")
        return output_path
