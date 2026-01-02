/*
 * PLM SolidWorks Add-in (C# / .NET Framework)
 * 
 * Responsibilities:
 * - Hook into SWKS API events (Save, SaveAs, Open, Close)
 * - Enforce project selection before save
 * - Capture metadata
 * - UI panels for version history, project selection, check-in/out
 * 
 * Requirements:
 * - SolidWorks 2020 or later
 * - .NET Framework 4.8 or later
 * - SolidWorks Primary Interop Assemblies (PIAs)
 */

using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swpublished;
using SolidWorks.Interop.swconst;

namespace PLM_SolidWorks_AddIn
{
    /// <summary>
    /// Main add-in class that integrates with SolidWorks
    /// </summary>
    [ComVisible(true)]
    [Guid("YOUR-GUID-HERE-REPLACE-ME")]
    public class PLMAddIn : ISwAddin
    {
        // SolidWorks application instance
        private ISldWorks _iSwApp;
        private int _iAddinID;
        
        // PLM system instance
        private PLMVaultManager _vaultManager;
        private PLMUIManager _uiManager;
        
        // Event handlers
        private SldWorksEvents_Event _swEvents;
        
        // Configuration
        private const string VAULT_ROOT = @"e:\PLM_VAULT";
        
        /// <summary>
        /// Called when add-in is loaded
        /// </summary>
        public bool OnConnect(SldWorks iSwApp, int iAddinID, int iAddinVersion)
        {
            _iSwApp = iSwApp;
            _iAddinID = iAddinID;
            
            try
            {
                // Initialize PLM system
                _vaultManager = new PLMVaultManager(VAULT_ROOT);
                _uiManager = new PLMUIManager(_iSwApp);
                
                // Register event handlers
                _swEvents = (SldWorksEvents_Event)_iSwApp;
                _swEvents.DocumentSave += OnDocumentSave;
                _swEvents.DocumentSaveAs += OnDocumentSaveAs;
                _swEvents.DocumentOpen += OnDocumentOpen;
                _swEvents.DocumentClose += OnDocumentClose;
                
                System.Diagnostics.Debug.WriteLine("PLM Add-in connected successfully");
                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error connecting PLM Add-in: {ex.Message}");
                return false;
            }
        }
        
        /// <summary>
        /// Called when add-in is unloaded
        /// </summary>
        public void OnDisconnect()
        {
            try
            {
                // Unregister event handlers
                if (_swEvents != null)
                {
                    _swEvents.DocumentSave -= OnDocumentSave;
                    _swEvents.DocumentSaveAs -= OnDocumentSaveAs;
                    _swEvents.DocumentOpen -= OnDocumentOpen;
                    _swEvents.DocumentClose -= OnDocumentClose;
                }
                
                System.Diagnostics.Debug.WriteLine("PLM Add-in disconnected");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error disconnecting PLM Add-in: {ex.Message}");
            }
        }
        
        // ================================================================
        // EVENT HANDLERS
        // ================================================================
        
        /// <summary>
        /// Intercepts Save event
        /// Flow: User clicks Save → Add-in validates → Saves to vault
        /// </summary>
        private int OnDocumentSave(ModelDoc2 doc)
        {
            try
            {
                System.Diagnostics.Debug.WriteLine($"OnDocumentSave: {doc.GetTitle()}");
                
                string filePath = doc.GetPathName();
                if (string.IsNullOrEmpty(filePath))
                    return 0; // Unsaved file, ignore
                
                // Check if file is in vault
                if (!IsFileInVault(filePath))
                {
                    // Show project selector UI
                    var projectId = _uiManager.ShowProjectSelector();
                    if (projectId <= 0)
                        return 1; // Cancel save
                }
                
                // Get file metadata from SWKS
                var metadata = ExtractMetadata(doc);
                
                // Check lock status
                var lockInfo = _vaultManager.CheckLockStatus(filePath);
                if (lockInfo.IsLocked && lockInfo.LockedBy != Environment.UserName)
                {
                    _uiManager.ShowError($"File locked by {lockInfo.LockedBy} since {lockInfo.LockTime}");
                    return 1; // Cancel save
                }
                
                // Check lifecycle state
                var fileInfo = _vaultManager.GetFileInfo(filePath);
                if (fileInfo != null && fileInfo.LifecycleState == "Released")
                {
                    _uiManager.ShowError("File is released (read-only). Create new major version to edit.");
                    return 1; // Cancel save
                }
                
                // Perform save to vault
                var result = _vaultManager.SaveToVault(filePath, metadata);
                
                if (result.Success)
                {
                    _uiManager.UpdateStatusBar(
                        $"v{result.VersionNumber} - {result.LifecycleState} - Checked out to {Environment.UserName}"
                    );
                    _uiManager.RefreshVersionHistory(filePath);
                }
                else
                {
                    _uiManager.ShowError($"Save failed: {result.Message}");
                    return 1; // Cancel save
                }
                
                return 0; // Success
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in OnDocumentSave: {ex.Message}");
                _uiManager.ShowError($"Save error: {ex.Message}");
                return 1;
            }
        }
        
        /// <summary>
        /// Intercepts Save As event
        /// </summary>
        private int OnDocumentSaveAs(ModelDoc2 doc, string FileName)
        {
            // Treat as a save operation
            return OnDocumentSave(doc);
        }
        
        /// <summary>
        /// Called when document is opened
        /// </summary>
        private int OnDocumentOpen(ModelDoc2 doc)
        {
            try
            {
                System.Diagnostics.Debug.WriteLine($"OnDocumentOpen: {doc.GetTitle()}");
                
                string filePath = doc.GetPathName();
                if (string.IsNullOrEmpty(filePath))
                    return 0;
                
                // Check if file is in vault
                if (!IsFileInVault(filePath))
                    return 0;
                
                // Get file info
                var fileInfo = _vaultManager.GetFileInfo(filePath);
                if (fileInfo == null)
                    return 0;
                
                // If released, make read-only
                if (fileInfo.LifecycleState == "Released")
                {
                    MakeDocumentReadOnly(doc);
                    _uiManager.ShowMessage($"File is released (read-only). Version: {fileInfo.CurrentVersion}");
                }
                
                // If assembly, resolve component references
                if (doc.GetType() == (int)swDocumentTypes_e.swDocASSEMBLY)
                {
                    ResolveAssemblyReferences((AssemblyDoc)doc);
                }
                
                // Show version history
                _uiManager.ShowVersionHistory(filePath);
                
                // Update status bar
                _uiManager.UpdateStatusBar(
                    $"v{fileInfo.CurrentVersion} - {fileInfo.LifecycleState} - {(fileInfo.LockedBy == null ? "Available" : $"Locked by {fileInfo.LockedBy}")}"
                );
                
                return 0;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in OnDocumentOpen: {ex.Message}");
                return 0; // Non-critical
            }
        }
        
        /// <summary>
        /// Called when document is closed
        /// </summary>
        private int OnDocumentClose()
        {
            try
            {
                System.Diagnostics.Debug.WriteLine("OnDocumentClose");
                
                // Clean up UI
                _uiManager.ClearVersionHistory();
                
                return 0;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error in OnDocumentClose: {ex.Message}");
                return 0;
            }
        }
        
        // ================================================================
        // HELPER METHODS
        // ================================================================
        
        /// <summary>
        /// Check if file is in vault directory
        /// </summary>
        private bool IsFileInVault(string filePath)
        {
            return filePath.StartsWith(VAULT_ROOT, StringComparison.OrdinalIgnoreCase);
        }
        
        /// <summary>
        /// Extract metadata from SWKS document
        /// </summary>
        private Dictionary<string, object> ExtractMetadata(ModelDoc2 doc)
        {
            var metadata = new Dictionary<string, object>();
            
            try
            {
                // Basic properties
                metadata["title"] = doc.GetTitle();
                metadata["author"] = Environment.UserName;
                metadata["timestamp"] = DateTime.UtcNow.ToString("o");
                
                // Custom properties
                var swCustomPropMgr = doc.Extension.CustomPropertyManager[""];
                if (swCustomPropMgr != null)
                {
                    // Example: read Material property
                    swCustomPropMgr.Get("Material", out string materialValue);
                    if (!string.IsNullOrEmpty(materialValue))
                        metadata["Material"] = materialValue;
                    
                    swCustomPropMgr.Get("Weight", out string weightValue);
                    if (!string.IsNullOrEmpty(weightValue))
                        metadata["Weight"] = weightValue;
                }
                
                // Configuration info
                metadata["Configuration"] = doc.GetActiveConfiguration().GetName();
                
                // File type
                switch (doc.GetType())
                {
                    case (int)swDocumentTypes_e.swDocPART:
                        metadata["FileType"] = "PART";
                        break;
                    case (int)swDocumentTypes_e.swDocASSEMBLY:
                        metadata["FileType"] = "ASSEMBLY";
                        break;
                    case (int)swDocumentTypes_e.swDocDRAWING:
                        metadata["FileType"] = "DRAWING";
                        break;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error extracting metadata: {ex.Message}");
            }
            
            return metadata;
        }
        
        /// <summary>
        /// Make document read-only (enforce lifecycle lock)
        /// </summary>
        private void MakeDocumentReadOnly(ModelDoc2 doc)
        {
            try
            {
                // SWKS doesn't have direct read-only API, so we:
                // 1. Hide Save button in UI
                // 2. Prevent OnSave from executing
                // 3. Show warning message
                
                _uiManager.DisableSaveButton();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error making document read-only: {ex.Message}");
            }
        }
        
        /// <summary>
        /// Resolve assembly component references (by PLM ID)
        /// </summary>
        private void ResolveAssemblyReferences(AssemblyDoc assembly)
        {
            try
            {
                // Read references.json from vault
                var references = _vaultManager.ReadAssemblyReferences(assembly.GetPathName());
                if (references == null)
                    return;
                
                // For each component, resolve vault path
                foreach (var component in references.Components)
                {
                    string vaultPath = _vaultManager.ResolveComponentPath(
                        component.ComponentPLMID,
                        component.ComponentVersion
                    );
                    
                    if (vaultPath == null)
                        System.Diagnostics.Debug.WriteLine($"Warning: Could not resolve {component.ComponentPLMID}");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error resolving assembly references: {ex.Message}");
            }
        }
    }
    
    
    /// <summary>
    /// Vault manager (handles vault operations)
    /// STUB: Will be implemented with calls to Python backend
    /// </summary>
    public class PLMVaultManager
    {
        private string _vaultRoot;
        
        public PLMVaultManager(string vaultRoot)
        {
            _vaultRoot = vaultRoot;
        }
        
        public bool IsFileInVault(string filePath) => filePath.StartsWith(_vaultRoot);
        
        public class LockInfo
        {
            public bool IsLocked { get; set; }
            public string LockedBy { get; set; }
            public DateTime LockTime { get; set; }
        }
        
        public LockInfo CheckLockStatus(string filePath)
        {
            // TODO: Query database via REST API or Python subprocess
            return new LockInfo { IsLocked = false };
        }
        
        public class FileInfo
        {
            public int CurrentVersion { get; set; }
            public string LifecycleState { get; set; }
            public string LockedBy { get; set; }
        }
        
        public FileInfo GetFileInfo(string filePath)
        {
            // TODO: Query database
            return null;
        }
        
        public class SaveResult
        {
            public bool Success { get; set; }
            public string Message { get; set; }
            public int VersionNumber { get; set; }
            public string LifecycleState { get; set; }
        }
        
        public SaveResult SaveToVault(string filePath, Dictionary<string, object> metadata)
        {
            // TODO: Implement vault save logic
            // 1. Get next version number
            // 2. Create version directory
            // 3. Copy file to vault
            // 4. Create metadata.json
            // 5. Update database
            
            return new SaveResult { Success = true, VersionNumber = 1 };
        }
        
        public class AssemblyReferences
        {
            public List<ComponentReference> Components { get; set; }
        }
        
        public class ComponentReference
        {
            public string ComponentPLMID { get; set; }
            public int ComponentVersion { get; set; }
            public string ComponentFileName { get; set; }
        }
        
        public AssemblyReferences ReadAssemblyReferences(string assemblyPath)
        {
            // TODO: Read references.json from vault
            return null;
        }
        
        public string ResolveComponentPath(string componentPLMID, int version)
        {
            // TODO: Query database for vault path
            return null;
        }
    }
    
    
    /// <summary>
    /// UI manager (handles user interface)
    /// </summary>
    public class PLMUIManager
    {
        private ISldWorks _swApp;
        private TaskpaneView _taskpaneView;
        
        public PLMUIManager(ISldWorks swApp)
        {
            _swApp = swApp;
        }
        
        public int ShowProjectSelector()
        {
            // TODO: Show dialog for project selection
            return 1;
        }
        
        public void ShowError(string message)
        {
            _swApp.SendMsgToUser(message);
        }
        
        public void ShowMessage(string message)
        {
            _swApp.SendMsgToUser(message);
        }
        
        public void UpdateStatusBar(string text)
        {
            // TODO: Update SolidWorks status bar
        }
        
        public void RefreshVersionHistory(string filePath)
        {
            // TODO: Refresh version history panel in taskpane
        }
        
        public void ShowVersionHistory(string filePath)
        {
            // TODO: Show version history in taskpane
        }
        
        public void ClearVersionHistory()
        {
            // TODO: Clear version history panel
        }
        
        public void DisableSaveButton()
        {
            // TODO: Hide/disable Save button for released files
        }
    }
}


/*
 * PROJECT FILE: PLM_SolidWorks_AddIn.csproj
 * 
 * <Project Sdk="Microsoft.NET.Sdk.WindowsDesktop">
 *   <PropertyGroup>
 *     <TargetFramework>net48</TargetFramework>
 *     <UseWindowsForms>true</UseWindowsForms>
 *     <OutputType>Library</OutputType>
 *     <GenerateSerializationAssemblies>On</GenerateSerializationAssemblies>
 *   </PropertyGroup>
 * 
 *   <ItemGroup>
 *     <Reference Include="SolidWorks.Interop.sldworks" />
 *     <Reference Include="SolidWorks.Interop.swconst" />
 *     <Reference Include="SolidWorks.Interop.swpublished" />
 *   </ItemGroup>
 * </Project>
 * 
 * REGISTRATION (run as admin):
 * C:\Windows\System32\regsvcs.exe "path\to\PLM_SolidWorks_AddIn.dll"
 */
