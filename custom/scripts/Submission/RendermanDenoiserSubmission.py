"""Renderman Denoiser submission script for Deadline"""

# encoding: utf-8

# pylint: disable=w0603, C0103, E0401, C0301, C0413

# Built-in
from __future__ import absolute_import
import re

# Third-Party
from Deadline.Scripting import ClientUtils, FrameUtils, PathUtils, RepositoryUtils
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog
from System.IO import File, Path, StreamWriter
from System.Collections.Specialized import StringCollection
from System.Text import Encoding

class RenderManDenoiserSubmissionDialog(DeadlineScriptDialog):
    """Custom dialog class for the RenderMan Denoiser submission script."""
    def __init__(self):
        """Initializes the RenderMan Denoiser submission dialog."""
        super().__init__()
        self._setup_ui()
        self.connect_signals()

    def _setup_ui(self):
        """Sets up the user interface for the RenderMan Denoiser submission dialog."""
        self.SetTitle("Submit RenderMan Denoiser Job To Deadline")
        self.SetIcon(self.GetIcon('RenderManDenoiser'))
        self.SetSize(900, 700)

        self.AddTabControl("Tabs", 0, 0)
        self.AddTabPage("Job Options")
        self.AddGrid()
        self.AddControlToGrid("Separator1", "SeparatorControl", "Job Description", 0, 0)
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid("NameLabel", "LabelControl", "Job Name", 0, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False)
        self.AddControlToGrid("NameBox", "TextControl", "Untitled", 0, 1)
        self.AddControlToGrid("CommentLabel", "LabelControl", "Comment", 1, 0, "A simple description of your job. This is optional and can be left blank.", False)
        self.AddControlToGrid("CommentBox", "TextControl", "", 1, 1)
        self.AddControlToGrid("DepartmentLabel", "LabelControl", "Department", 2, 0, "The department you belong to. This is optional and can be left blank.", False)
        self.AddControlToGrid("DepartmentBox", "TextControl", "", 2, 1)
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid("Separator2", "SeparatorControl", "Job Options", 0, 0)
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid("PoolLabel", "LabelControl", "Pool", 0, 0, "The pool that your job will be submitted to.", False)
        self.AddControlToGrid("PoolBox", "PoolComboControl", "none", 0, 1)
        self.AddControlToGrid("SecondaryPoolLabel", "LabelControl", "Secondary Pool", 1, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Workers.", False)
        self.AddControlToGrid("SecondaryPoolBox", "SecondaryPoolComboControl", "", 1, 1)
        self.AddControlToGrid("GroupLabel", "LabelControl", "Group", 2, 0, "The group that your job will be submitted to.", False)
        self.AddControlToGrid("GroupBox", "GroupComboControl", "none", 2, 1)
        self.AddControlToGrid("PriorityLabel", "LabelControl", "Priority", 3, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False)
        self.AddRangeControlToGrid("PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() // 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 3, 1)
        self.AddControlToGrid("TaskTimeoutLabel", "LabelControl", "Task Timeout", 4, 0, "The number of minutes a Worker has to render a task for this job before it requeues it. Specify 0 for no limit.", False)
        self.AddRangeControlToGrid("TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 4, 1)
        self.AddSelectionControlToGrid("AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 4, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. ")
        self.AddControlToGrid("ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0, "The number of tasks that can render concurrently on a single Worker. This is useful if the rendering application only uses one thread to render and your Workers have multiple CPUs.", False)
        self.AddRangeControlToGrid("ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 5, 1)
        self.AddSelectionControlToGrid("LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Worker's Task Limit", 5, 2, "If you limit the tasks to a Worker's task limit, then by default, the Worker won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Workers by an administrator.")
        self.AddControlToGrid("MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False)
        self.AddRangeControlToGrid("MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 6, 1)
        self.AddSelectionControlToGrid("IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Deny List", 6, 2, "You can force the job to render on specific machines by using an allow list, or you can avoid specific machines by using a deny list.")
        self.AddControlToGrid("MachineListLabel", "LabelControl", "Machine List", 7, 0, "The list of machines on the deny list or allow list.", False)
        self.AddControlToGrid("MachineListBox", "MachineListControl", "", 7, 1, colSpan=2)
        self.AddControlToGrid("LimitGroupLabel", "LabelControl", "Limit Groups", 8, 0, "The Limits that your job requires.", False)
        self.AddControlToGrid("LimitGroupBox", "LimitGroupControl", "", 8, 1, colSpan=2)
        self.AddControlToGrid("DependencyLabel", "LabelControl", "Dependencies", 9, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False)
        self.AddControlToGrid("DependencyBox", "DependencyControl", "", 9, 1, colSpan=2)
        self.AddControlToGrid("OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0, "If desired, you can automatically archive or delete the job when it completes.", False)
        self.AddControlToGrid("OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 10, 1)
        self.AddSelectionControlToGrid("SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 10, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.")
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid("Separator3", "SeparatorControl", "RenderMan Denoiser Options", 0, 0)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("RenderManVersionLabel", "LabelControl", "RenderMan Version", 0, 0, "The version of RenderMan to use.", False)
        self.AddRangeControlToGrid("RenderManVersionRange", "RangeControl", 27.2, 27.0, 27.2, 1, 0.1, 0, 1)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("BeautySequenceLabel", "LabelControl", "Beauty EXRs Sequence", 0, 0, "The EXRs sequence containing necessary aovs for denoising. Please refer to the RenderMan's documentation for more details.", False)
        self.AddSelectionControlToGrid("BeautyBox", "FileBrowserControl", "", "EXRs containing necessary aovs (*.exr)", 0, 1, colSpan=2)
        self.AddControlToGrid("LpeSequenceLabel", "LabelControl", "Lpe EXRs Sequence (Optional)", 1, 0, "The EXRs sequence containing LPE passes. Please refer to the RenderMan's documentation for more details.", False)
        self.AddSelectionControlToGrid("LpeBox", "FileBrowserControl", "", "EXRs containing aovs to denoise using the master (*.exr)", 1, 1, colSpan=2)
        self.AddControlToGrid("LgtSequenceLabel", "LabelControl", "Lgt EXRs Sequence (Optional)", 2, 0, "The EXRs sequence containing LGT passes. Please refer to the RenderMan's documentation for more details.", False)
        self.AddSelectionControlToGrid("LgtBox", "FileBrowserControl", "", "EXRs containing aovs to denoise using the master (*.exr)", 2, 1, colSpan=2)
        self.AddControlToGrid("OutputLabel","LabelControl","Output (optional)", 3, 0, "Override the output path for the denoised EXRs. This is optional, and can be left blank. Default is ./denoised", False)
        self.AddSelectionControlToGrid("OutputBox","FolderBrowserControl","", "All Files (*)",3, 1, colSpan=2)
        self.AddControlToGrid("AsymmetryLabel", "LabelControl", "Asymmetry", 4, 0, "Controls the asymmetry value. 0 is best quality, higher values encourage the denoiser to avoid overblurring, leading to weaker denoising.\nRequired=false", False)
        self.AddRangeControlToGrid("Asymmetry", "RangeControl", 0.0, 0.0, 1.0, 1, 0.1, 4, 1)
        self.AddControlToGrid("CrossFrameLabel", "LabelControl", "Cross-Frame Denoising", 5, 0, "Enable cross-frame denoising. Uses temporal information from neighboring frames to improve denoising quality.", False)
        self.AddSelectionControlToGrid("CrossFrame", "CheckBoxControl", True, "", 5, 1, colSpan=2)
        self.AddControlToGrid("FlowLabel", "LabelControl", "Flow", 6, 0, "Whether to compute optical flow. Used in conjunction with cross-frame denoising.", False)
        self.AddSelectionControlToGrid("Flow", "CheckBoxControl", True, "", 6, 1, colSpan=2)
        self.AddControlToGrid("CleanAlphaLabel", "LabelControl", "Clean Alpha", 7, 0, "Rounds alpha values less than 0.00001 and greater than 0.999. Helps reduce artifacts.", False)
        self.AddSelectionControlToGrid("CleanAlpha", "CheckBoxControl", True, "", 7, 1, colSpan=2)
        self.AddControlToGrid("FramesLabel", "LabelControl", "Frame List", 8, 0, "The list of frames to render.", False)
        self.AddControlToGrid("FramesBox", "TextControl", "", 8, 1, colSpan=2)
        self.AddControlToGrid("ChunkSizeLabel", "LabelControl", "Frames Per Task", 9, 0, "This is the number of frames that will be rendered at a time for each job task.", False)
        self.AddRangeControlToGrid("ChunkSizeBox", "RangeControl", 10, 1, 1000000, 0, 1, 9, 1)
        self.EndGrid()

        self.EndTabPage()

        # Advanced Tab
        self.AddTabPage("Advanced")

        # Denoising Options Section
        self.AddGrid()
        self.AddControlToGrid("AdvSeparator1", "SeparatorControl", "Denoising Options", 0, 0)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("JsonLabel", "LabelControl", "Use JSON Config", 0, 0, "If enabled, use the first input file as the configuration JSON file. All other files and options are ignored, except for: --frame-include, --frame-exclude, --tiles, --progress.", False)
        self.AddSelectionControlToGrid("JsonBox", "CheckBoxControl", False, "", 0, 1)
        self.AddControlToGrid("DryRunLabel", "LabelControl", "Dry Run", 1, 0, "Write the configuration JSON file, but don't run the denoiser. Useful for inspecting and modifying the configuration file before passing it back with the JSON flag.", False)
        self.AddSelectionControlToGrid("DryRunBox", "CheckBoxControl", False, "", 1, 1)
        self.AddControlToGrid("ProgressLabel", "LabelControl", "Emit Progress", 2, 0, "Emit a progress percentage. Compatible with LocalQueue and Tractor.", False)
        self.AddSelectionControlToGrid("ProgressBox", "CheckBoxControl", True, "", 2, 1)
        self.EndGrid()

        # Frame Options Section
        self.AddGrid()
        self.AddControlToGrid("AdvSeparator2", "SeparatorControl", "Frame Options", 0, 0)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("FrameIncludeLabel", "LabelControl", "Frame Include", 0, 0, "Include only specific frames in the denoising job. Comma-separated list of frame numbers or ranges. Ex: 1001-1008,1012,1013-", False)
        self.AddControlToGrid("FrameIncludeBox", "TextControl", "", 0, 1)
        self.AddControlToGrid("FrameExcludeLabel", "LabelControl", "Frame Exclude", 1, 0, "Exclude specific frames from the denoising job. Comma-separated list of frame numbers or ranges. Ex: -1002,1015", False)
        self.AddControlToGrid("FrameExcludeBox", "TextControl", "", 1, 1)
        self.EndGrid()

        # Channel Mapping Section
        self.AddGrid()
        self.AddControlToGrid("AdvSeparator3", "SeparatorControl", "Channel Mapping", 0, 0)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("SpecularLabel", "LabelControl", "Specular Channels", 0, 0, "Comma-separated list of channels to consider as specular outputs. Channels named 'transmissiveSingleScatterLobe' and 'transmissiveGlassLobe' are assumed specular by default. Ex: glass,my_glass_aov", False)
        self.AddControlToGrid("SpecularBox", "TextControl", "", 0, 1)
        self.AddControlToGrid("DiffuseLabel", "LabelControl", "Diffuse Channels", 1, 0, "Comma-separated list of channels to consider as diffuse outputs. Channels named 'subsurface' and 'subsurfaceLobe' are assumed diffuse by default. Ex: subsurf,my_sss_aov", False)
        self.AddControlToGrid("DiffuseBox", "TextControl", "", 1, 1)
        self.AddControlToGrid("AlbedoLabel", "LabelControl", "Albedo Channels", 2, 0, "Comma-separated list of channels to consider as albedo outputs. Ex: my_constant,my_emissive", False)
        self.AddControlToGrid("AlbedoBox", "TextControl", "", 2, 1)
        self.AddControlToGrid("IrradianceLabel", "LabelControl", "Irradiance Channels", 3, 0, "Comma-separated list of channels to consider as irradiance outputs. Ex: irr,my_irr", False)
        self.AddControlToGrid("IrradianceBox", "TextControl", "", 3, 1)
        self.AddControlToGrid("AlphaChannelLabel", "LabelControl", "Alpha Channels", 4, 0, "Comma-separated list of channels to consider as alpha outputs. Unknown channels of length 1 are automatically mapped to alpha. Ex: my_a,my_alpha", False)
        self.AddControlToGrid("AlphaChannelBox", "TextControl", "", 4, 1)
        self.AddControlToGrid("ColorLabel", "LabelControl", "Color Channels", 5, 0, "Comma-separated list of channels to consider as color outputs. Unknown channels of length 3 are automatically mapped to color. Ex: my_aov,my_output", False)
        self.AddControlToGrid("ColorBox", "TextControl", "", 5, 1)
        self.EndGrid()

        # Performance Section
        self.AddGrid()
        self.AddControlToGrid("AdvSeparator4", "SeparatorControl", "Performance", 0, 0)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("TilesXLabel", "LabelControl", "Tiles X", 0, 0, "Number of horizontal tiles. Denoising in tiles can reduce memory usage for large images, but may increase processing time.", False)
        self.AddRangeControlToGrid("TilesXBox", "RangeControl", 1, 1, 64, 0, 1, 0, 1)
        self.AddControlToGrid("TilesYLabel", "LabelControl", "Tiles Y", 1, 0, "Number of vertical tiles. Denoising in tiles can reduce memory usage for large images, but may increase processing time.", False)
        self.AddRangeControlToGrid("TilesYBox", "RangeControl", 1, 1, 64, 0, 1, 1, 1)
        self.EndGrid()

        self.AddGrid()
        self.AddControlToGrid("AdvSeparator5", "SeparatorControl", "Debug", 0, 0)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("DebugLabel", "LabelControl", "Debug AOVs", 0, 0, "If enabled, include debug AOVs in the output image for debugging.", False)
        self.AddSelectionControlToGrid("DebugBox", "CheckBoxControl", False, "", 0, 1)
        self.AddControlToGrid("DebugOutputLabel", "LabelControl", "Debug Output Filename", 1, 0, "If the Debug flag is enabled, this specifies the filename the debug AOVs should be written to in the output directory. If not specified, defaults to writing to the denoised variance file.", False)
        self.AddControlToGrid("DebugOutputBox", "TextControl", "", 1, 1)
        self.AddControlToGrid("VerboseLabel", "LabelControl", "Verbose Output", 2, 0, "Verbose output for debugging.", False)
        self.AddSelectionControlToGrid("VerboseBox", "CheckBoxControl", False, "", 2, 1)
        self.AddControlToGrid("TerseLabel", "LabelControl", "Terse Output", 3, 0, "Only print warnings and errors.", False)
        self.AddSelectionControlToGrid("TerseBox", "CheckBoxControl", False, "", 3, 1)
        self.EndGrid()

        # Command Line Options Section
        self.AddGrid()
        self.AddControlToGrid("AdvSeparator6", "SeparatorControl", "Command Line Options", 0, 0)
        self.EndGrid()
        self.AddGrid()
        self.AddControlToGrid("CommandLineLabel", "LabelControl", "Additional Arguments", 0, 0, "Additional command line arguments that are sent to the denoise_batch executable.", False)
        self.AddControlToGrid("CommandLineBox", "TextControl", "", 0, 1)
        self.EndGrid()

        self.EndTabPage()
        self.EndTabControl()
        self.AddGrid()
        self.AddHorizontalSpacerToGrid("HSpacer1", 0, 0)
        self.submit_button = self.AddControlToGrid("SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False)
        self.close_button = self.AddControlToGrid("CloseButton", "ButtonControl", "Close", 0, 2, expand=False)

        self.EndGrid()

        self.settings = (
            "DepartmentBox",
            "PoolBox",
            "SecondaryPoolBox",
            "GroupBox",
            "PriorityBox",
            "MachineLimitBox",
            "IsBlacklistBox",
            "MachineListBox",
            "LimitGroupBox",
            "FramesBox",
            "ChunkSizeBox",
            "OutputBox",
            "RenderManVersionRange",
            "BeautyBox",
            "LpeBox",
            "LgtBox",
            "Asymmetry",
            "CrossFrame",
            "Flow",
            "CleanAlpha",
            # Advanced
            "JsonBox",
            "DryRunBox",
            "ProgressBox",
            "FrameIncludeBox",
            "FrameExcludeBox",
            "SpecularBox",
            "DiffuseBox",
            "AlbedoBox",
            "IrradianceBox",
            "AlphaChannelBox",
            "ColorBox",
            "TilesXBox",
            "TilesYBox",
            "DebugBox",
            "DebugOutputBox",
            "VerboseBox",
            "TerseBox",
            "CommandLineBox"
        )

        self.LoadSettings(self.get_settings_filename(), self.settings)
        self.EnabledStickySaving(self.settings, self.get_settings_filename())

    def connect_signals(self):
        """Connects the signals for the UI controls."""
        self.close_button.ValueModified.connect(self.closeEvent)
        self.submit_button.ValueModified.connect(self.submit_button_pressed)

    def get_settings_filename(self) -> str:
        """Returns the path to the settings file for the RenderMan Denoiser submission dialog."""
        return Path.Combine(
        ClientUtils.GetUsersSettingsDirectory(),
        "RenderManDenoiserSettings.ini"
       )

    def create_job_info_file(self, frames: str, output_dir: str) -> str:
        """Creates the job info file for the RenderMan Denoiser submission."""
        # Get job name
        job_name = self.GetValue("NameBox").strip()

        # Create job info file
        job_info_filename = Path.Combine(ClientUtils.GetDeadlineTempPath(), "renderman_denoiser_job_info.job")
        writer = StreamWriter(job_info_filename, False, Encoding.Unicode)

        writer.WriteLine("Plugin=RenderManDenoiser")
        writer.WriteLine(f"Name={job_name}")
        writer.WriteLine(f"Comment={self.GetValue('CommentBox')}")
        writer.WriteLine(f"Department={self.GetValue('DepartmentBox')}")
        writer.WriteLine(f"Pool={self.GetValue('PoolBox')}")
        writer.WriteLine(f"SecondaryPool={self.GetValue('SecondaryPoolBox')}")
        writer.WriteLine(f"Group={self.GetValue('GroupBox')}")
        writer.WriteLine(f"Priority={self.GetValue('PriorityBox')}")
        writer.WriteLine(f"TaskTimeoutMinutes={self.GetValue('TaskTimeoutBox')}")
        writer.WriteLine(f"EnableAutoTimeout={self.GetValue('AutoTimeoutBox')}")
        writer.WriteLine(f"ConcurrentTasks={self.GetValue('ConcurrentTasksBox')}")
        writer.WriteLine(f"LimitConcurrentTasksToNumberOfCpus={self.GetValue('LimitConcurrentTasksBox')}")
        writer.WriteLine(f"MachineLimit={self.GetValue('MachineLimitBox')}")

        if bool(self.GetValue("IsBlacklistBox")):
            writer.WriteLine(f"Blacklist={self.GetValue('MachineListBox')}")
        else:
            writer.WriteLine(f"Whitelist={self.GetValue('MachineListBox')}")

        writer.WriteLine(f"LimitGroups={self.GetValue('LimitGroupBox')}")
        writer.WriteLine(f"JobDependencies={self.GetValue('DependencyBox')}")
        writer.WriteLine(f"OnJobComplete={self.GetValue('OnJobCompleteBox')}")

        if bool(self.GetValue("SubmitSuspendedBox")):
            writer.WriteLine("InitialStatus=Suspended")

        writer.WriteLine(f"Frames={frames}")
        writer.WriteLine(f"ChunkSize={self.GetValue('ChunkSizeBox')}")

        if len(output_dir) > 0:
            writer.WriteLine(f"OutputDirectory0={output_dir}")
        writer.WriteLine(f"BatchName={job_name}\n")
        writer.Close()

        return job_info_filename

    def check_frame_pattern(self, path: str) -> bool:
        """Checks if the given path uses a .####.exr hash frame pattern."""
        return bool(re.search(r'\.#+\.exr$', path, re.IGNORECASE))

    def has_frame_number(self, path: str) -> bool:
        """Checks if the path contains a numeric frame pattern like .0001.exr."""
        return bool(re.search(r'\.\d+\.exr$', path, re.IGNORECASE))

    def convert_to_frame_pattern(self, path: str) -> str:
        """Converts a frame number in a path to a hash pattern.

        E.g., 'image.0001.exr' -> 'image.####.exr'
        Returns the path unchanged if no frame number pattern is found.
        """
        return re.sub(
            r'\.(\d+)\.exr$',
            lambda m: '.' + '#' * len(m.group(1)) + '.exr',
            path,
            flags=re.IGNORECASE
        )

    def create_plugin_info_file(self, output_dir: str, beauty_file: str, lpe_file: str, lgt_file: str) -> str:
        """Creates the plugin info file for the RenderMan Denoiser submission."""
        plugin_info_filename = Path.Combine(ClientUtils.GetDeadlineTempPath(), "renderman_denoiser_plugin_info.job")
        writer = StreamWriter(plugin_info_filename, False, Encoding.Unicode)

        # RenderMan Version
        version = self.GetValue("RenderManVersionRange")
        writer.WriteLine(f"RenderManVersion={version}")

        # RenderMan Denoiser Input Files
        writer.WriteLine(f"BeautyFile={beauty_file}")
        beauty_dir = Path.GetDirectoryName(beauty_file)

        files_to_check = [
            (lpe_file, "LpeFile",
            "The Lpe EXRs sequence must be in the same directory as the Beauty EXRs sequence. The Lpe EXRs will be ignored."),
            (lgt_file, "LgtFile",
            "The Lgt EXRs sequence must be in the same directory as the Beauty EXRs sequence. The Lgt EXRs will be ignored."),
        ]
        for file_path, output_key, warning_msg in files_to_check:
            if not file_path:
                continue
            if Path.GetDirectoryName(file_path) == beauty_dir:
                writer.WriteLine(f"{output_key}={file_path}")
            else:
                self.ShowMessageBox(warning_msg, "Warning")

        if len(output_dir) > 0:
            writer.WriteLine(f"OutputDirectory={output_dir}")

        writer.WriteLine(f"Asymmetry={self.GetValue('Asymmetry')}")
        writer.WriteLine(f"CrossFrame={self.GetValue('CrossFrame')}")
        writer.WriteLine(f"Flow={self.GetValue('Flow')}")
        writer.WriteLine(f"CleanAlpha={self.GetValue('CleanAlpha')}")

        # Advanced Options - Denoising Options
        writer.WriteLine(f"Json={self.GetValue('JsonBox')}")
        writer.WriteLine(f"DryRun={self.GetValue('DryRunBox')}")
        writer.WriteLine(f"Progress={self.GetValue('ProgressBox')}")

        # Advanced Options - Frame Options
        frame_options = {
            "FrameIncludeBox": "FrameInclude",
            "FrameExcludeBox": "FrameExclude",
        }

        # Advanced Options - Channel Mapping
        channel_mapping = {
            "SpecularBox": "Specular",
            "DiffuseBox": "Diffuse",
            "AlbedoBox": "Albedo",
            "IrradianceBox": "Irradiance",
            "AlphaChannelBox": "Alpha",
            "ColorBox": "Color",
        }

        # Merge both dictionaries if you want a single loop
        all_options = {**frame_options, **channel_mapping}

        for ui_key, output_key in all_options.items():
            value = self.GetValue(ui_key).strip()
            if value:
                writer.WriteLine(f"{output_key}={value}")

        # Advanced Options - Debug
        writer.WriteLine(f"Debug={self.GetValue('DebugBox')}")

        debug_output = self.GetValue("DebugOutputBox").strip()
        if len(debug_output) > 0:
            writer.WriteLine(f"DebugOutput={debug_output}")

        writer.WriteLine(f"Verbose={self.GetValue('VerboseBox')}")
        writer.WriteLine(f"Terse={self.GetValue('TerseBox')}")

        # Advanced Options - Command Line
        command_line = self.GetValue("CommandLineBox").strip()
        if len(command_line) > 0:
            writer.WriteLine(f"CommandLineOptions={command_line}")

        writer.Close()
        return plugin_info_filename

    def submit_button_pressed(self):
        """Handles the logic for when the submit button is pressed."""
        beauty_file = self.GetValue("BeautyBox").strip()
        if len(beauty_file) == 0:
            self.ShowMessageBox("Please specify the Beauty EXRs sequence.", "Error")
            return

        if PathUtils.IsPathLocal(beauty_file):
            result = self.ShowMessageBox(
                f"The Beauty file {beauty_file} is local, are you sure you want to continue ?",
                "Warning",
                ("Yes", "No")
            )
            if result == "No":
                return

        frames = self.GetValue("FramesBox").strip()
        if len(frames) == 0 or not FrameUtils.FrameRangeValid(frames):
            self.ShowMessageBox(f"Frame range '{frames}' is not valid", "Error")
            return

        output_dir = self.GetValue("OutputBox").strip()
        if len(output_dir) > 0 and PathUtils.IsPathLocal(output_dir):
            result = self.ShowMessageBox(
            f"The output directory {output_dir} is local, are you sure you want to continue ?",
            "Warning",
            ("Yes", "No")
            )
            if result == "No":
                return

        # Validate and convert frame patterns for multi-frame jobs
        lpe_file = self.GetValue("LpeBox").strip()
        lgt_file = self.GetValue("LgtBox").strip()

        is_single_frame = len(FrameUtils.Parse(frames)) == 1

        if not is_single_frame:
            paths_to_validate = [("Beauty", beauty_file)]
            if lpe_file:
                paths_to_validate.append(("Lpe", lpe_file))
            if lgt_file:
                paths_to_validate.append(("Lgt", lgt_file))

            for label, file_path in paths_to_validate:
                if not self.check_frame_pattern(file_path) and not self.has_frame_number(file_path):
                    self.ShowMessageBox(
                        f"The {label} EXRs sequence must match a .####.exr or .0001.exr frame pattern.",
                        "Error"
                    )
                    return

            # Convert any numeric frame patterns (e.g. .0001.exr) to hash patterns (.####.exr)
            beauty_file = self.convert_to_frame_pattern(beauty_file)
            if lpe_file:
                lpe_file = self.convert_to_frame_pattern(lpe_file)
            if lgt_file:
                lgt_file = self.convert_to_frame_pattern(lgt_file)

        # Create job info file
        job_info_filename = self.create_job_info_file(frames, output_dir)

        # Create plugin info file
        plugin_info_filename = self.create_plugin_info_file(output_dir, beauty_file, lpe_file, lgt_file)

        # Setup the command line arguments.
        arguments = StringCollection()

        arguments.Add(job_info_filename)
        arguments.Add(plugin_info_filename)

        # Now submit the job.
        results = ClientUtils.ExecuteCommandAndGetOutput(arguments)
        self.ShowMessageBox(results, "Submission Results")

def __main__():
    """Main function called by Deadline when the script is executed."""
    dialog = RenderManDenoiserSubmissionDialog()
    dialog.ShowDialog()
