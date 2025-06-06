from obswebsocket import obsws, requests


class OBSRecorder:
    def __init__(
        self,
        obs_config: dict[str],
    ):
        """
        Initializes the OBSRecorder with the scene name and connection parameters.
        Arguments of obs_config:
            scene_name (str): Name of the scene to switch to and record.
            host (str): Hostname for OBS WebSocket (default: "localhost").
            port (int): Port for OBS WebSocket (default: 4488).
            password (str): Password for OBS WebSocket (if you set one in OBS).
            record_dir (str): Directory to save recordings. Default is default OBS directory.
        """
        self.scene_name = obs_config["scene_name"]
        self.host = obs_config["host"]
        self.port = obs_config["port"]
        self.password = obs_config["password"]
        self.ws = obsws(self.host, self.port, self.password, authreconnect=1)
        self.ws.connect()
        self.ws.call(requests.SetCurrentProgramScene(sceneName=self.scene_name))

        self.obs_init_dir = self.ws.call(requests.GetRecordDirectory()).datain["recordDirectory"]
        self.record_dir = obs_config["record_dir"]
        if self.record_dir:
            self.ws.call(requests.SetRecordDirectory(recordDirectory=self.record_dir))

    def start_recording(self):
        """
        Connects to an existing OBS instance (via WebSocket) and starts recording
        on the given scene.
        """
        self.ws.call(requests.StartRecord())

    def stop_recording(self):
        """
        Stops the recording in the connected OBS instance and disconnects.

        Args:
            ws (obsws): The OBS WebSocket client returned by start_recording().
        """
        self.ws.call(requests.StopRecord())

    def destroy(self):
        """
        Disconnects from the OBS WebSocket server.
        """
        is_recording = self.ws.call(requests.GetRecordStatus()).datain["outputActive"]
        if is_recording:
            self.stop_recording()

        if self.record_dir:
            self.ws.call(requests.SetRecordDirectory(recordDirectory=self.obs_init_dir))
        self.ws.disconnect()
