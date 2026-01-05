using System;

namespace PLMAddIn.Models
{
    /// <summary>
    /// Represents metadata for a single version snapshot
    /// </summary>
    public class VersionInfo
    {
        public string Version { get; set; }
        public string FileName { get; set; }
        public string Author { get; set; }
        public DateTime Timestamp { get; set; }
        public long FileSize { get; set; }
        public string Notes { get; set; }
        public string FilePath { get; set; }
        public bool IsLocked { get; set; }
    }
}
