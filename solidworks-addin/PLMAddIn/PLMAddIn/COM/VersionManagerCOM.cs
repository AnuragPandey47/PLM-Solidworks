using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using PLMAddIn.Models;
using PLMAddIn.Services;

namespace PLMAddIn.COM
{
    /// <summary>
    /// COM-visible wrapper for VersionManager - accessible from Python via COM interop
    /// </summary>
    [Guid("C9F0A1E4-5D6B-7E8A-9F0D-1C2B3A4E5D6F")]
    [ClassInterface(ClassInterfaceType.None)]
    [ComVisible(true)]
    [ProgId("PLMAddIn.VersionManagerCOM")]
    public class VersionManagerCOM : IVersionManagerCOM
    {
        private readonly VersionManager _versionManager;

        public VersionManagerCOM()
        {
            _versionManager = new VersionManager();
        }

        /// <summary>
        /// Creates a new version from the working directory
        /// </summary>
        /// <param name="projectPath">Full path to project directory (e.g., D:\Projects\MyProject)</param>
        /// <param name="fileName">File name (e.g., Part1.SLDPRT)</param>
        /// <param name="changeNote">Version change notes</param>
        /// <returns>JSON string with version info</returns>
        public string CreateVersion(string projectPath, string fileName, string changeNote)
        {
            try
            {
                string workingFilePath = Path.Combine(projectPath, "working", fileName);
                
                if (!File.Exists(workingFilePath))
                {
                    return SerializeError($"Working file not found: {workingFilePath}");
                }

                var versionInfo = _versionManager.CreateVersion(workingFilePath, changeNote);
                return SerializeVersionInfo(versionInfo);
            }
            catch (Exception ex)
            {
                return SerializeError(ex.Message);
            }
        }

        /// <summary>
        /// Gets version history for a file
        /// </summary>
        /// <param name="projectPath">Full path to project directory</param>
        /// <param name="fileName">File name</param>
        /// <returns>JSON array of version info</returns>
        public string GetVersionHistory(string projectPath, string fileName)
        {
            try
            {
                string workingFilePath = Path.Combine(projectPath, "working", fileName);
                var versions = _versionManager.GetVersionHistory(workingFilePath);
                return SerializeVersionList(versions);
            }
            catch (Exception ex)
            {
                return SerializeError(ex.Message);
            }
        }

        /// <summary>
        /// Makes a version immutable (read-only)
        /// </summary>
        /// <param name="projectPath">Full path to project directory</param>
        /// <param name="fileName">File name</param>
        /// <param name="versionNumber">Version number (e.g., v001)</param>
        /// <returns>True if successful</returns>
        public bool FreezeVersion(string projectPath, string fileName, string versionNumber)
        {
            try
            {
                string versionFilePath = Path.Combine(projectPath, "vault", versionNumber, fileName);
                
                if (!File.Exists(versionFilePath))
                    return false;

                var fileService = new FileService();
                fileService.SetReadOnly(versionFilePath, true);
                return true;
            }
            catch
            {
                return false;
            }
        }

        /// <summary>
        /// Gets the latest version number for a file
        /// </summary>
        public string GetLatestVersion(string projectPath, string fileName)
        {
            try
            {
                string workingFilePath = Path.Combine(projectPath, "working", fileName);
                var versions = _versionManager.GetVersionHistory(workingFilePath);
                
                if (versions.Count == 0)
                    return "v000";

                return versions.Last().Version;
            }
            catch
            {
                return "v000";
            }
        }

        #region JSON Serialization Helpers

        private string SerializeVersionInfo(VersionInfo version)
        {
            return $@"{{
  ""success"": true,
  ""version"": ""{version.Version}"",
  ""fileName"": ""{version.FileName}"",
  ""author"": ""{version.Author}"",
  ""timestamp"": ""{version.Timestamp:yyyy-MM-ddTHH:mm:ss}"",
  ""fileSize"": {version.FileSize},
  ""notes"": ""{EscapeJson(version.Notes)}"",
  ""filePath"": ""{EscapeJson(version.FilePath)}"",
  ""isLocked"": {version.IsLocked.ToString().ToLower()}
}}";
        }

        private string SerializeVersionList(List<VersionInfo> versions)
        {
            if (versions.Count == 0)
            {
                return @"{ ""success"": true, ""versions"": [] }";
            }

            var sb = new StringBuilder();
            sb.AppendLine(@"{ ""success"": true, ""versions"": [");

            for (int i = 0; i < versions.Count; i++)
            {
                var v = versions[i];
                sb.Append($@"  {{
    ""version"": ""{v.Version}"",
    ""fileName"": ""{v.FileName}"",
    ""author"": ""{v.Author}"",
    ""timestamp"": ""{v.Timestamp:yyyy-MM-ddTHH:mm:ss}"",
    ""fileSize"": {v.FileSize},
    ""notes"": ""{EscapeJson(v.Notes)}"",
    ""filePath"": ""{EscapeJson(v.FilePath)}"",
    ""isLocked"": {v.IsLocked.ToString().ToLower()}
  }}");
                
                if (i < versions.Count - 1)
                    sb.AppendLine(",");
                else
                    sb.AppendLine();
            }

            sb.AppendLine("]}");
            return sb.ToString();
        }

        private string SerializeError(string message)
        {
            return $@"{{ ""success"": false, ""error"": ""{EscapeJson(message)}"" }}";
        }

        private string EscapeJson(string text)
        {
            if (string.IsNullOrEmpty(text))
                return "";

            return text.Replace("\\", "\\\\")
                       .Replace("\"", "\\\"")
                       .Replace("\n", "\\n")
                       .Replace("\r", "\\r");
        }

        #endregion
    }
}
