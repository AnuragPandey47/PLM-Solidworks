using System;
using System.IO;

namespace PLMAddIn.Services
{
    /// <summary>
    /// Handles PLM metadata storage and retrieval using JSON
    /// </summary>
    public class MetadataService
    {
        private const string PartMetaFileName = "part_meta.json";
        private const string VersionMetaFileName = "version_meta.json";

        /// <summary>
        /// Updates or creates part_meta.json in the part folder
        /// </summary>
        public void UpdatePartMetadata(string partMetaFolder, string state, string latestVersion, string releasedVersion)
        {
            if (!Directory.Exists(partMetaFolder))
                Directory.CreateDirectory(partMetaFolder);

            string metadataPath = Path.Combine(partMetaFolder, PartMetaFileName);

            string releasedVersionValue = releasedVersion ?? "null";
            string json = $@"{{
  ""latest_version"": ""{latestVersion}"",
  ""released_version"": {releasedVersionValue},
  ""state"": ""{state}""
}}";

            File.WriteAllText(metadataPath, json);
        }

        /// <summary>
        /// Creates version_meta.json in a version folder
        /// </summary>
        public void CreateVersionMetadata(string versionFolder, string version, string author, string changeNote)
        {
            if (!Directory.Exists(versionFolder))
                Directory.CreateDirectory(versionFolder);

            string metadataPath = Path.Combine(versionFolder, VersionMetaFileName);

            string timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ");
            string json = $@"{{
  ""version"": ""{version}"",
  ""created_by"": ""{author}"",
  ""created_timestamp"": ""{timestamp}"",
  ""change_note"": ""{EscapeJson(changeNote)}"",
  ""state"": ""Frozen""
}}";

            File.WriteAllText(metadataPath, json);
        }

        /// <summary>
        /// Loads part metadata from part_meta.json
        /// </summary>
        public PartMetadata LoadPartMetadata(string partMetaFolder)
        {
            string metadataPath = Path.Combine(partMetaFolder, PartMetaFileName);

            if (!File.Exists(metadataPath))
                return null;

            try
            {
                string json = File.ReadAllText(metadataPath);
                return ParsePartMetadata(json);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading part metadata: {ex.Message}");
                return null;
            }
        }

        /// <summary>
        /// Simple JSON parser for PartMetadata
        /// </summary>
        private PartMetadata ParsePartMetadata(string json)
        {
            var metadata = new PartMetadata();
            
            metadata.LatestVersion = ExtractValue(json, "latest_version");
            metadata.ReleasedVersion = ExtractValue(json, "released_version");
            metadata.State = ExtractValue(json, "state");
            
            return metadata;
        }

        private string ExtractValue(string json, string key)
        {
            string pattern = $"\"{key}\": \"";
            int start = json.IndexOf(pattern);
            if (start == -1)
            {
                // Try null pattern
                pattern = $"\"{key}\": ";
                start = json.IndexOf(pattern);
                if (start == -1) return "";
                start += pattern.Length;
                int end = json.IndexOfAny(new[] { ',', '}', '\n' }, start);
                string value = json.Substring(start, end - start).Trim();
                return value == "null" ? null : value;
            }
            
            start += pattern.Length;
            int end2 = json.IndexOf("\"", start);
            return json.Substring(start, end2 - start);
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
    }

    /// <summary>
    /// Part metadata structure
    /// </summary>
    public class PartMetadata
    {
        public string LatestVersion { get; set; }
        public string ReleasedVersion { get; set; }
        public string State { get; set; }
    }
}
