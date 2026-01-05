using System;
using System.IO;
using PLMAddIn.Services;

namespace PLMAddIn.Lifecycle
{
    /// <summary>
    /// Handles PLM lifecycle operations: Freeze, Release, Rework
    /// </summary>
    public class LifecycleManager
    {
        private readonly MetadataService _metadataService;
        private readonly FileService _fileService;

        public LifecycleManager()
        {
            _metadataService = new MetadataService();
            _fileService = new FileService();
        }

        /// <summary>
        /// Freezes current working copy as a new version
        /// </summary>
        public string FreezeVersion(string projectPath, string fileName, string changeNote)
        {
            try
            {
                string fileNameWithoutExt = Path.GetFileNameWithoutExtension(fileName);
                string workingFilePath = Path.Combine(projectPath, "Working", "Parts", fileName);

                if (!File.Exists(workingFilePath))
                    throw new FileNotFoundException($"Working file not found: {workingFilePath}");

                // Get part metadata folder
                string partMetaFolder = Path.Combine(projectPath, "Parts", fileNameWithoutExt);
                
                // Load current metadata to get next version number
                var currentMeta = _metadataService.LoadPartMetadata(partMetaFolder);
                string nextVersion = GetNextVersionNumber(currentMeta?.LatestVersion);

                // Create version folder
                string versionFolder = Path.Combine(partMetaFolder, nextVersion);
                Directory.CreateDirectory(versionFolder);

                // Copy working file to version folder
                string versionFilePath = Path.Combine(versionFolder, fileName);
                File.Copy(workingFilePath, versionFilePath, overwrite: true);

                // Make version file read-only (immutable)
                _fileService.SetReadOnly(versionFilePath, true);

                // Create version_meta.json
                string author = System.Environment.UserName;
                _metadataService.CreateVersionMetadata(versionFolder, nextVersion, author, changeNote);

                // Update part_meta.json
                _metadataService.UpdatePartMetadata(partMetaFolder, "Frozen", nextVersion, currentMeta?.ReleasedVersion);

                return nextVersion;
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to freeze version: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Releases a specific version (marks as approved)
        /// </summary>
        public void ReleaseVersion(string projectPath, string fileName, string versionNumber)
        {
            try
            {
                string fileNameWithoutExt = Path.GetFileNameWithoutExtension(fileName);
                string partMetaFolder = Path.Combine(projectPath, "Parts", fileNameWithoutExt);

                // Verify version exists
                string versionFolder = Path.Combine(partMetaFolder, versionNumber);
                if (!Directory.Exists(versionFolder))
                    throw new DirectoryNotFoundException($"Version not found: {versionNumber}");

                // Load current metadata
                var currentMeta = _metadataService.LoadPartMetadata(partMetaFolder);
                if (currentMeta == null)
                    throw new Exception("Part metadata not found");

                // Update part_meta.json with released version
                _metadataService.UpdatePartMetadata(partMetaFolder, "Released", currentMeta.LatestVersion, versionNumber);

                // Lock the released version file (make read-only)
                string versionFilePath = Path.Combine(versionFolder, fileName);
                if (File.Exists(versionFilePath))
                {
                    _fileService.SetReadOnly(versionFilePath, true);
                }
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to release version: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Reworks from a frozen version (copies back to working)
        /// </summary>
        public void ReworkVersion(string projectPath, string fileName, string versionNumber)
        {
            try
            {
                string fileNameWithoutExt = Path.GetFileNameWithoutExtension(fileName);
                string versionFilePath = Path.Combine(projectPath, "Parts", fileNameWithoutExt, versionNumber, fileName);

                if (!File.Exists(versionFilePath))
                    throw new FileNotFoundException($"Version file not found: {versionFilePath}");

                // Copy version back to working directory
                string workingFilePath = Path.Combine(projectPath, "Working", "Parts", fileName);
                File.Copy(versionFilePath, workingFilePath, overwrite: true);

                // Ensure working copy is NOT read-only
                if (File.Exists(workingFilePath))
                {
                    _fileService.SetReadOnly(workingFilePath, false);
                }

                // Update part_meta.json to Working state
                string partMetaFolder = Path.Combine(projectPath, "Parts", fileNameWithoutExt);
                var currentMeta = _metadataService.LoadPartMetadata(partMetaFolder);
                _metadataService.UpdatePartMetadata(partMetaFolder, "Working", currentMeta?.LatestVersion, currentMeta?.ReleasedVersion);
            }
            catch (Exception ex)
            {
                throw new Exception($"Failed to rework version: {ex.Message}", ex);
            }
        }

        /// <summary>
        /// Gets current state of a part
        /// </summary>
        public string GetPartState(string projectPath, string fileName)
        {
            try
            {
                string fileNameWithoutExt = Path.GetFileNameWithoutExtension(fileName);
                string partMetaFolder = Path.Combine(projectPath, "Parts", fileNameWithoutExt);

                var metadata = _metadataService.LoadPartMetadata(partMetaFolder);
                return metadata?.State ?? "Working";
            }
            catch
            {
                return "Unknown";
            }
        }

        private string GetNextVersionNumber(string currentVersion)
        {
            if (string.IsNullOrEmpty(currentVersion) || currentVersion == "v000")
                return "v001";

            // Parse current version number
            if (currentVersion.StartsWith("v") && currentVersion.Length == 4)
            {
                if (int.TryParse(currentVersion.Substring(1), out int versionNum))
                {
                    return $"v{(versionNum + 1):D3}";
                }
            }

            return "v001";
        }
    }
}
