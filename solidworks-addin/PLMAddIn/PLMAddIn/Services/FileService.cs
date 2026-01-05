using System;
using System.IO;

namespace PLMAddIn.Services
{
    /// <summary>
    /// Handles file operations (copy, read-only, etc.)
    /// </summary>
    public class FileService
    {
        /// <summary>
        /// Sets or removes read-only attribute on a file
        /// </summary>
        public void SetReadOnly(string filePath, bool isReadOnly)
        {
            if (!File.Exists(filePath))
                throw new FileNotFoundException("File not found", filePath);

            FileAttributes attributes = File.GetAttributes(filePath);

            if (isReadOnly)
            {
                attributes |= FileAttributes.ReadOnly;
            }
            else
            {
                attributes &= ~FileAttributes.ReadOnly;
            }

            File.SetAttributes(filePath, attributes);
        }

        /// <summary>
        /// Checks if a file is read-only
        /// </summary>
        public bool IsReadOnly(string filePath)
        {
            if (!File.Exists(filePath))
                return false;

            FileAttributes attributes = File.GetAttributes(filePath);
            return (attributes & FileAttributes.ReadOnly) == FileAttributes.ReadOnly;
        }

        /// <summary>
        /// Copies a file and optionally makes it read-only
        /// </summary>
        public void CopyFile(string sourceFile, string destFile, bool makeReadOnly = false)
        {
            if (!File.Exists(sourceFile))
                throw new FileNotFoundException("Source file not found", sourceFile);

            // Ensure destination directory exists
            string destDir = Path.GetDirectoryName(destFile);
            if (!Directory.Exists(destDir))
            {
                Directory.CreateDirectory(destDir);
            }

            // Copy the file
            File.Copy(sourceFile, destFile, overwrite: true);

            // Set read-only if requested
            if (makeReadOnly)
            {
                SetReadOnly(destFile, true);
            }
        }

        /// <summary>
        /// Gets file size in bytes
        /// </summary>
        public long GetFileSize(string filePath)
        {
            if (!File.Exists(filePath))
                return 0;

            FileInfo fileInfo = new FileInfo(filePath);
            return fileInfo.Length;
        }
    }
}
