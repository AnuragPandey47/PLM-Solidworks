using System;
using System.Runtime.InteropServices;

namespace PLMAddIn.COM
{
    /// <summary>
    /// COM interface for VersionManager - accessible from Python
    /// </summary>
    [Guid("B8E9F0D3-4C5B-6E7A-8F9D-0C1B2A3E4D5F")]
    [InterfaceType(ComInterfaceType.InterfaceIsIDispatch)]
    [ComVisible(true)]
    public interface IVersionManagerCOM
    {
        [DispId(1)]
        string CreateVersion(string projectPath, string fileName, string changeNote);

        [DispId(2)]
        string GetVersionHistory(string projectPath, string fileName);

        [DispId(3)]
        bool FreezeVersion(string projectPath, string fileName, string versionNumber);

        [DispId(4)]
        string GetLatestVersion(string projectPath, string fileName);
    }
}
