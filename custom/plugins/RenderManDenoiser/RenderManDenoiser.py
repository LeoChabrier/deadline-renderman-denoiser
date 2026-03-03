#!/usr/bin/env python3
"""RenderMan Denoiser plugin for Deadline.

This plugin executes the denoise_batch executable from RenderMan
to denoise EXR image sequences.
"""
# pylint: disable=C0103
from __future__ import absolute_import

import sys

from Deadline.Plugins import DeadlinePlugin
from Deadline.Scripting import RepositoryUtils, SystemUtils


def GetDeadlinePlugin():
    """Returns an instance of the RenderManDenoiser plugin."""
    return RenderManDenoiserPlugin()


def CleanupDeadlinePlugin(deadline_plugin):
    """Cleans up the RenderManDenoiser plugin."""
    deadline_plugin.Cleanup()


class RenderManDenoiserPlugin(DeadlinePlugin):
    """Deadline plugin for RenderMan Denoiser."""

    def __init__(self):
        """Initializes the RenderMan Denoiser plugin."""
        if sys.version_info.major == 3:
            super().__init__()
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks

    def Cleanup(self):
        """Cleans up the plugin callbacks."""
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback

    def InitializeProcess(self):
        """Initializes the process settings and stdout handlers."""
        self.SingleFramesOnly = False
        self.StdoutHandling = True

        # Progress handler for RenderMan denoiser (when --progress is enabled)
        self.AddStdoutHandlerCallback(
            r".*Progress: (\d+(?:\.\d+)?)%.*"
        ).HandleCallback += self.HandleProgress

        # Alternative progress format
        self.AddStdoutHandlerCallback(
            r".*(\d+(?:\.\d+)?)% complete.*"
        ).HandleCallback += self.HandleProgress

        # Frame completion handler
        self.AddStdoutHandlerCallback(
            r".*Denoised frame (\d+).*"
        ).HandleCallback += self.HandleFrameComplete

        # Error handlers
        self.AddStdoutHandlerCallback(
            r".*[Ee]rror:.*"
        ).HandleCallback += self.HandleStdoutError

        self.AddStdoutHandlerCallback(
            r".*[Ff]ailed.*"
        ).HandleCallback += self.HandleStdoutError

        self.AddStdoutHandlerCallback(
            r".*[Nn]o such file.*"
        ).HandleCallback += self.HandleStdoutError

        self.AddStdoutHandlerCallback(
            r".*[Cc]annot open.*"
        ).HandleCallback += self.HandleStdoutError

    def RenderExecutable(self):
        """Returns the path to the denoise_batch executable."""
        version = self.GetPluginInfoEntryWithDefault("RenderManVersion", "27.2")
        return self.GetRenderExecutable(f"RenderMan_{version}_DenoiseBatch")

    def RenderArgument(self):
        """Builds and returns the command line arguments for denoise_batch."""
        arguments = []

        # Get input files from plugin info
        beauty_file = self.GetPluginInfoEntryWithDefault("BeautyFile", "")
        beauty_file = RepositoryUtils.CheckPathMapping(beauty_file)
        beauty_file = self._normalize_path(beauty_file)

        if not beauty_file:
            self.FailRender("No Beauty file specified.")
            return ""

        # Add beauty file (required)
        arguments.append(f'"{beauty_file}"')

        # Add optional LPE file
        lpe_file = self.GetPluginInfoEntryWithDefault("LpeFile", "")
        if lpe_file:
            lpe_file = RepositoryUtils.CheckPathMapping(lpe_file)
            lpe_file = self._normalize_path(lpe_file)
            arguments.append(f'"{lpe_file}"')

        # Add optional LGT file
        lgt_file = self.GetPluginInfoEntryWithDefault("LgtFile", "")
        if lgt_file:
            lgt_file = RepositoryUtils.CheckPathMapping(lgt_file)
            lgt_file = self._normalize_path(lgt_file)
            arguments.append(f'"{lgt_file}"')

        # Add frame range
        start_frame = self.GetStartFrame()
        end_frame = self.GetEndFrame()
        arguments.append(f"{start_frame}-{end_frame}")

        # Output directory
        output_dir = self.GetPluginInfoEntryWithDefault("OutputDirectory", "")
        if output_dir:
            output_dir = RepositoryUtils.CheckPathMapping(output_dir)
            output_dir = self._normalize_path(output_dir)
            arguments.append(f'--output "{output_dir}"')

        # Asymmetry
        asymmetry = self.GetPluginInfoEntryWithDefault("Asymmetry", "")
        if asymmetry:
            arguments.append(f"--asymmetry {asymmetry}")

        # Boolean flags
        if self.GetBooleanPluginInfoEntryWithDefault("CrossFrame", False):
            arguments.append("--crossframe")

        if self.GetBooleanPluginInfoEntryWithDefault("Flow", False):
            arguments.append("--flow")

        if self.GetBooleanPluginInfoEntryWithDefault("CleanAlpha", False):
            arguments.append("--clean-alpha")

        if self.GetBooleanPluginInfoEntryWithDefault("Json", False):
            arguments.append("--json")

        if self.GetBooleanPluginInfoEntryWithDefault("DryRun", False):
            arguments.append("--dry-run")

        if self.GetBooleanPluginInfoEntryWithDefault("Progress", True):
            arguments.append("--progress")

        # Frame include/exclude
        frame_include = self.GetPluginInfoEntryWithDefault("FrameInclude", "")
        if frame_include:
            arguments.append(f"--frame-include {frame_include}")

        frame_exclude = self.GetPluginInfoEntryWithDefault("FrameExclude", "")
        if frame_exclude:
            arguments.append(f"--frame-exclude {frame_exclude}")

        # Channel mappings
        specular = self.GetPluginInfoEntryWithDefault("Specular", "")
        if specular:
            arguments.append(f"--specular {specular}")

        diffuse = self.GetPluginInfoEntryWithDefault("Diffuse", "")
        if diffuse:
            arguments.append(f"--diffuse {diffuse}")

        albedo = self.GetPluginInfoEntryWithDefault("Albedo", "")
        if albedo:
            arguments.append(f"--albedo {albedo}")

        irradiance = self.GetPluginInfoEntryWithDefault("Irradiance", "")
        if irradiance:
            arguments.append(f"--irradiance {irradiance}")

        alpha = self.GetPluginInfoEntryWithDefault("Alpha", "")
        if alpha:
            arguments.append(f"--alpha {alpha}")

        color = self.GetPluginInfoEntryWithDefault("Color", "")
        if color:
            arguments.append(f"--color {color}")

        # Tiles
        tiles_x = self.GetIntegerPluginInfoEntryWithDefault("TilesX", 1)
        tiles_y = self.GetIntegerPluginInfoEntryWithDefault("TilesY", 1)
        if tiles_x > 1 or tiles_y > 1:
            arguments.append(f"--tiles {tiles_x} {tiles_y}")

        # Debug options
        if self.GetBooleanPluginInfoEntryWithDefault("Debug", False):
            arguments.append("--debug")

            debug_output = self.GetPluginInfoEntryWithDefault("DebugOutput", "")
            if debug_output:
                debug_output = RepositoryUtils.CheckPathMapping(debug_output)
                debug_output = self._normalize_path(debug_output)
                arguments.append(f'--debug-output "{debug_output}"')

        # Verbosity flags
        if self.GetBooleanPluginInfoEntryWithDefault("Verbose", False):
            arguments.append("--verbose")

        if self.GetBooleanPluginInfoEntryWithDefault("Terse", False):
            arguments.append("--terse")

        # Additional command line options
        extra_args = self.GetPluginInfoEntryWithDefault("CommandLineOptions", "")
        if extra_args:
            arguments.append(extra_args)

        return " ".join(arguments)

    def _normalize_path(self, path):
        """Normalizes a path based on the current operating system."""
        if not path:
            return path

        if SystemUtils.IsRunningOnWindows():
            path = path.replace("/", "\\")
            if path.startswith("\\") and not path.startswith("\\\\"):
                path = "\\" + path
        else:
            path = path.replace("\\", "/")

        return path

    def PreRenderTasks(self):
        """Called before render tasks begin."""
        self.LogInfo("RenderMan Denoiser job starting...")

        # Initialize progress tracking
        self.totalFrames = self.GetEndFrame() - self.GetStartFrame() + 1
        self.finishedFrames = 0
        self.currentProgress = 0.0

    def PostRenderTasks(self):
        """Called after render tasks complete."""
        self.LogInfo("RenderMan Denoiser job finished.")

    def HandleProgress(self):
        """Handles progress percentage output from denoise_batch."""
        progress = float(self.GetRegexMatch(1))
        self.SetProgress(progress)
        self.SetStatusMessage(f"Denoising: {progress:.1f}%")

    def HandleFrameComplete(self):
        """Handles frame completion output."""
        frame = int(self.GetRegexMatch(1))
        self.finishedFrames += 1
        self.LogInfo(f"Completed denoising frame {frame}")

    def HandleStdoutError(self):
        """Handles error output from denoise_batch."""
        error_message = self.GetRegexMatch(0)
        self.LogWarning(f"Potential error detected: {error_message}")
