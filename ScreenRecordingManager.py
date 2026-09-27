from datetime import datetime
from pyscreenrec import ScreenRecorder
from functools import wraps
import pytest
import os
import json

class ScreenRecorderManager:
    def __init__(self, test_name, output_filename=None, fps=30, user_context=None):
        # Load country configuration
        self.user_context = user_context
        # self.country_code = self.user_context.country_code if self.user_context else 'default'
        self.country_code = 'co'
        
        # Load the country configuration
        self.country_config = self.load_country_config()
        self.country_settings = self.country_config.get(self.country_code, {})

        # Create videos directory if it doesn't exist
        base_dir = 'videos'
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            
        # Create country-specific directory
        country_dir = os.path.join(base_dir, self.country_code)
        if not os.path.exists(country_dir):
            os.makedirs(country_dir)
        
        if output_filename is None:
            self.output_filename = os.path.join('videos', self.country_code, f"{self.country_code}_recording_{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
        else:
            self.output_filename = output_filename
        
        self.fps = fps  # Store the fps value
        self.recorder = ScreenRecorder()

    def start_recording(self):
        self.recorder.start_recording(self.output_filename, fps=self.fps)  # Pass fps to start_recording

    def stop_recording(self):
        self.recorder.stop_recording()
    
    def load_country_config(self, file_path='country_config_am.json'):
        """Load the country configuration from a JSON file."""
        with open(file_path, encoding='utf-8') as config_file:
            return json.load(config_file)
ScreenRecorder.country_code = 'ci'
def record_test(fps=30, output_filename=None):
    """Decorator to record the test execution."""
    def decorator(test_func):
        @wraps(test_func)
        def wrapper(*args, **kwargs):
            test_name = test_func.__name__
            user_context = None
            
            if args and isinstance(args[0], tuple) and len(args[0]) > 1:
                _, user_context = args[0]
                print(f"Extracted User Context: {user_context}")  # Debugging output
            else:
                print("Warning: User context not found in arguments.")
                user_context = None
            
            # Create an instance of ScreenRecorderManager with the user context
            recorder = ScreenRecorderManager(test_name=test_name, output_filename=output_filename, fps=fps, user_context=user_context)
            recorder.start_recording()
            try:
                result = test_func(*args, **kwargs)
            finally:
                recorder.stop_recording()
            return result
        return wrapper
    return decorator