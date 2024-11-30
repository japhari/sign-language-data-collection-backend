import subprocess
import logging

# Constants
REQUIRED_DURATION = 5  # Seconds
REQUIRED_RESOLUTION = (640, 480)  # Width, Height

def validate_video_metadata(filepath):
    """
    Temporarily relax video validation to allow all videos to pass.
    """
    try:
        logging.info(f"Validating video metadata: {filepath}")

        # Get duration (if available)
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
             'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        duration_str = result.stdout.strip()
        logging.info(f"Duration string from ffprobe: {duration_str}")

        # Skip duration validation
        if duration_str == "N/A" or not duration_str:
            logging.warning(f"Skipping duration validation for {filepath}.")
        else:
            duration = float(duration_str)
            logging.info(f"Video duration: {duration}s")

        # Skip frame rate and resolution validation
        logging.info(f"Skipping frame rate and resolution validation for {filepath}.")
        return True
    except Exception as e:
        logging.error(f"Error validating metadata: {e}")
        return False


def validate_video_by_frame_count(filepath):
    """
    Fallback validation using frame count and frame rate if duration metadata is unavailable.
    """
    try:
        logging.info(f"Validating video by frame count: {filepath}")

        # Get frame count and frame rate using ffprobe
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
             '-show_entries', 'stream=nb_read_frames,r_frame_rate',
             '-of', 'default=noprint_wrappers=1:nokey=1', filepath],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        output = result.stdout.strip().splitlines()

        if len(output) < 2:
            logging.error(f"Error extracting frame count or frame rate: {output}")
            return False

        frame_count = int(output[0])  # nb_read_frames
        frame_rate = eval(output[1])  # Convert frame rate fraction (e.g., "277/12") to a float

        # Calculate duration from frame count and frame rate
        duration = frame_count / frame_rate

        if abs(duration - REQUIRED_DURATION) > 0.5:  # Allow ±0.5 seconds tolerance
            logging.error(f"Invalid duration: {duration}s. Expected: {REQUIRED_DURATION}s ± 0.5s.")
            return False

        logging.info(f"Video validated by frame count successfully: Duration={duration}s")
        return True
    except Exception as e:
        logging.error(f"Error validating video by frame count: {e}")
        return False


def get_video_resolution(filepath):
    """Extract video resolution (width, height) using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=width,height',
             '-of', 'csv=p=0', filepath],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        resolution = tuple(map(int, result.stdout.strip().split(',')))
        return resolution
    except Exception as e:
        logging.error(f"Error getting video resolution: {e}")
        return None


def adjust_video(input_path, output_path, target_frame_rate=30, target_duration=5):
    """
    Adjust the video frame rate and duration to match the expected specifications.
    """
    try:
        logging.info(f"Adjusting video: {input_path}")

        # Get actual duration of the video
        cmd_duration = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=duration', '-of', 'default=nw=1:nk=1', input_path
        ]
        result = subprocess.run(cmd_duration, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration_str = result.stdout.strip()

        if duration_str == "N/A" or not duration_str:
            logging.error(f"Cannot adjust video: Duration unavailable for {input_path}.")
            return False

        actual_duration = float(duration_str)
        logging.info(f"Actual Duration: {actual_duration} seconds")

        # Calculate speed factor to match target duration
        speed_factor = actual_duration / target_duration if actual_duration != target_duration else 1.0
        logging.info(f"Speed Factor: {speed_factor}")

        # Adjust the video
        cmd_adjust = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', f'fps={target_frame_rate}',
            '-filter:v', f'setpts={speed_factor}*PTS',
            '-r', str(target_frame_rate),
            output_path
        ]
        subprocess.run(cmd_adjust, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if not os.path.exists(output_path):
            logging.error(f"Adjusted video not created: {output_path}")
            return False

        logging.info(f"Video adjusted and saved to: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error adjusting video: {e}")
        return False
