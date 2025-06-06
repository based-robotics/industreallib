#!/usr/bin/env python3
"""
rosbag_recorder.py

A simple Python wrapper for non-blocking rosbag recording in ROS Noetic.
Provides a RosbagRecorder class with methods to start and stop recording.
"""

import subprocess
import signal
import os
import time
import subprocess
import signal
import os
import time


class RosbagRecorder:
    """
    Wraps rosbag record in a non-blocking subprocess. Allows starting
    and stopping a recording via start_recording() and stop_recording().
    """

    def __init__(self):
        """
        Initialize the recorder.

        Args:
            topics (list of str): List of topic names to record.
            bag_name (str): Base name (without .bag) for the output bag file.
            output_dir (str, optional): Directory in which to save .bag file.
                                        Defaults to current working directory.
            record_args (list of str, optional): Additional command-line
                arguments to pass to `rosbag record` (e.g., ['--lz4']).
        """
        self._process = None  # Will hold the subprocess.Popen object

    def start_recording(self):
        """
        Start rosbag recording in a non-blocking manner. Spawns a subprocess
        that runs `rosbag record`. If a recording is already running,
        raises a RuntimeError.
        """
        if self._process is not None and self._process.poll() is None:
            raise RuntimeError("A rosbag recording is already in progress.")

        cmd = ["rosbag", "record", "-a"]

        self._process = subprocess.Popen(
            cmd,
            preexec_fn=os.setsid,  # put the process in its own session (Unix only)
        )

        # Small delay to give rosbag record time to start
        time.sleep(0.2)

        if self._process.poll() is not None:
            # If the process terminated immediately, capture return code
            retcode = self._process.returncode
            self._process = None
            raise RuntimeError(f"Failed to start rosbag record (exit code {retcode}).")

    def stop_recording(self, timeout=5.0):
        """
        Stop the running rosbag recording by sending SIGINT. Waits up to
        `timeout` seconds for the subprocess to exit cleanly. If no recording
        is in progress, raises a RuntimeError.

        Args:
            timeout (float): Maximum seconds to wait for the subprocess to exit
                             after sending SIGINT. Defaults to 5 seconds.
        """
        if self._process is None or self._process.poll() is not None:
            raise RuntimeError("No active rosbag recording to stop.")

        # Send SIGINT to the process group to allow rosbag to close the bag properly
        pgid = os.getpgid(self._process.pid)
        os.killpg(pgid, signal.SIGINT)

        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # If rosbag doesn't exit in time, forcefully terminate
            os.killpg(pgid, signal.SIGTERM)
            self._process.wait()

        finally:
            self._process = None
