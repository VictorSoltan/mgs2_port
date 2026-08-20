/* Generated abort stubs for the native ARM WineD3D island inside Box86.
 *
 * Win32/GDI/setup entry points the island links against but must never call.
 * Excluded: symbols box86 itself defines, and everything libc/libm/pthread
 * provides. An earlier version omitted the libc set and stubbed memcpy,
 * memset, strlen, getenv and the float maths with abort(), which killed box86
 * before it printed its banner. The box86 set must come from its object files,
 * not from a linked binary that already contains the island -- that filter is
 * circular and empties the list. Regenerate, never hand-edit.
 *
 * Also excluded, because mgs2_island_natives.c implements them for real and a
 * second definition breaks the link:
 *   _assert  _fdclass  __wine_dbg_get_channel_flags  __wine_dbg_header
 *   __wine_dbg_output  __wine_dbg_strdup  __stdio_common_vsprintf
 *   TlsGetValue  TlsSetValue  WindowFromDC
 *   wglCreateContext  wglDeleteContext  wglGetCurrentContext  wglGetCurrentDC
 *   wglGetProcAddress  wglMakeCurrent  wglShareLists
 * _recalloc is NOT in that set and stays an abort stub on purpose: it would
 * have to resize a block whose allocator is unknown. */
extern int printf(const char *, ...);
extern void abort(void);

static void mgs2_island_forbidden(const char *n)
{
    printf("MGS2 island: forbidden call to %s\n", n);
    abort();
}

void AdjustWindowRectEx(void) { mgs2_island_forbidden("AdjustWindowRectEx"); }
void AllocateLocallyUniqueId(void) { mgs2_island_forbidden("AllocateLocallyUniqueId"); }
void BitBlt(void) { mgs2_island_forbidden("BitBlt"); }
void CallNextHookEx(void) { mgs2_island_forbidden("CallNextHookEx"); }
void CallWindowProcA(void) { mgs2_island_forbidden("CallWindowProcA"); }
void CallWindowProcW(void) { mgs2_island_forbidden("CallWindowProcW"); }
void ChangeDisplaySettingsExW(void) { mgs2_island_forbidden("ChangeDisplaySettingsExW"); }
void ChoosePixelFormat(void) { mgs2_island_forbidden("ChoosePixelFormat"); }
void ClientToScreen(void) { mgs2_island_forbidden("ClientToScreen"); }
void CloseHandle(void) { mgs2_island_forbidden("CloseHandle"); }
void CreateBitmap(void) { mgs2_island_forbidden("CreateBitmap"); }
void CreateCompatibleDC(void) { mgs2_island_forbidden("CreateCompatibleDC"); }
void CreateDCW(void) { mgs2_island_forbidden("CreateDCW"); }
void CreateEventW(void) { mgs2_island_forbidden("CreateEventW"); }
void CreateIconIndirect(void) { mgs2_island_forbidden("CreateIconIndirect"); }
void CreateThread(void) { mgs2_island_forbidden("CreateThread"); }
void CreateWindowExA(void) { mgs2_island_forbidden("CreateWindowExA"); }
void D3DKMTCloseAdapter(void) { mgs2_island_forbidden("D3DKMTCloseAdapter"); }
void D3DKMTCreateDCFromMemory(void) { mgs2_island_forbidden("D3DKMTCreateDCFromMemory"); }
void D3DKMTCreateDevice(void) { mgs2_island_forbidden("D3DKMTCreateDevice"); }
void D3DKMTDestroyDCFromMemory(void) { mgs2_island_forbidden("D3DKMTDestroyDCFromMemory"); }
void D3DKMTDestroyDevice(void) { mgs2_island_forbidden("D3DKMTDestroyDevice"); }
void D3DKMTEscape(void) { mgs2_island_forbidden("D3DKMTEscape"); }
void D3DKMTOpenAdapterFromGdiDisplayName(void) { mgs2_island_forbidden("D3DKMTOpenAdapterFromGdiDisplayName"); }
void D3DKMTOpenAdapterFromLuid(void) { mgs2_island_forbidden("D3DKMTOpenAdapterFromLuid"); }
void D3DKMTQueryVideoMemoryInfo(void) { mgs2_island_forbidden("D3DKMTQueryVideoMemoryInfo"); }
void D3DKMTSetVidPnSourceOwner(void) { mgs2_island_forbidden("D3DKMTSetVidPnSourceOwner"); }
void DebugBreak(void) { mgs2_island_forbidden("DebugBreak"); }
void DefWindowProcA(void) { mgs2_island_forbidden("DefWindowProcA"); }
void DefWindowProcW(void) { mgs2_island_forbidden("DefWindowProcW"); }
void DeleteCriticalSection(void) { mgs2_island_forbidden("DeleteCriticalSection"); }
void DeleteDC(void) { mgs2_island_forbidden("DeleteDC"); }
void DeleteObject(void) { mgs2_island_forbidden("DeleteObject"); }
void DescribePixelFormat(void) { mgs2_island_forbidden("DescribePixelFormat"); }
void DestroyCursor(void) { mgs2_island_forbidden("DestroyCursor"); }
void DestroyWindow(void) { mgs2_island_forbidden("DestroyWindow"); }
void DisableThreadLibraryCalls(void) { mgs2_island_forbidden("DisableThreadLibraryCalls"); }
void EnterCriticalSection(void) { mgs2_island_forbidden("EnterCriticalSection"); }
void EnumDisplayDevicesW(void) { mgs2_island_forbidden("EnumDisplayDevicesW"); }
void EnumDisplayMonitors(void) { mgs2_island_forbidden("EnumDisplayMonitors"); }
void EnumDisplaySettingsExW(void) { mgs2_island_forbidden("EnumDisplaySettingsExW"); }
void EnumDisplaySettingsW(void) { mgs2_island_forbidden("EnumDisplaySettingsW"); }
void FindResourceA(void) { mgs2_island_forbidden("FindResourceA"); }
void FreeLibrary(void) { mgs2_island_forbidden("FreeLibrary"); }
void FreeLibraryAndExitThread(void) { mgs2_island_forbidden("FreeLibraryAndExitThread"); }
void FreeResource(void) { mgs2_island_forbidden("FreeResource"); }
void GetClientRect(void) { mgs2_island_forbidden("GetClientRect"); }
void GetCursorPos(void) { mgs2_island_forbidden("GetCursorPos"); }
void GetDC(void) { mgs2_island_forbidden("GetDC"); }
void GetDCEx(void) { mgs2_island_forbidden("GetDCEx"); }
void GetDesktopWindow(void) { mgs2_island_forbidden("GetDesktopWindow"); }
void GetDeviceGammaRamp(void) { mgs2_island_forbidden("GetDeviceGammaRamp"); }
void GetModuleFileNameA(void) { mgs2_island_forbidden("GetModuleFileNameA"); }
void GetModuleHandleA(void) { mgs2_island_forbidden("GetModuleHandleA"); }
void GetModuleHandleExA(void) { mgs2_island_forbidden("GetModuleHandleExA"); }
void GetModuleHandleExW(void) { mgs2_island_forbidden("GetModuleHandleExW"); }
void GetModuleHandleW(void) { mgs2_island_forbidden("GetModuleHandleW"); }
void GetMonitorInfoW(void) { mgs2_island_forbidden("GetMonitorInfoW"); }
void GetObjectA(void) { mgs2_island_forbidden("GetObjectA"); }
void GetPixelFormat(void) { mgs2_island_forbidden("GetPixelFormat"); }
void GetProcAddress(void) { mgs2_island_forbidden("GetProcAddress"); }
void GetVersionExW(void) { mgs2_island_forbidden("GetVersionExW"); }
void GetWindowLongA(void) { mgs2_island_forbidden("GetWindowLongA"); }
void GetWindowLongW(void) { mgs2_island_forbidden("GetWindowLongW"); }
void GetWindowRect(void) { mgs2_island_forbidden("GetWindowRect"); }
void GetWindowThreadProcessId(void) { mgs2_island_forbidden("GetWindowThreadProcessId"); }
void GlobalMemoryStatusEx(void) { mgs2_island_forbidden("GlobalMemoryStatusEx"); }
void HeapAlloc(void) { mgs2_island_forbidden("HeapAlloc"); }
void HeapCreate(void) { mgs2_island_forbidden("HeapCreate"); }
void HeapDestroy(void) { mgs2_island_forbidden("HeapDestroy"); }
void HeapFree(void) { mgs2_island_forbidden("HeapFree"); }
void InitializeCriticalSectionEx(void) { mgs2_island_forbidden("InitializeCriticalSectionEx"); }
void IntersectRect(void) { mgs2_island_forbidden("IntersectRect"); }
void IsBadStringPtrA(void) { mgs2_island_forbidden("IsBadStringPtrA"); }
void IsBadStringPtrW(void) { mgs2_island_forbidden("IsBadStringPtrW"); }
void IsWindow(void) { mgs2_island_forbidden("IsWindow"); }
void IsWindowUnicode(void) { mgs2_island_forbidden("IsWindowUnicode"); }
void IsWindowVisible(void) { mgs2_island_forbidden("IsWindowVisible"); }
void KillTimer(void) { mgs2_island_forbidden("KillTimer"); }
void LeaveCriticalSection(void) { mgs2_island_forbidden("LeaveCriticalSection"); }
void LoadCursorA(void) { mgs2_island_forbidden("LoadCursorA"); }
void LoadIconA(void) { mgs2_island_forbidden("LoadIconA"); }
void LoadImageA(void) { mgs2_island_forbidden("LoadImageA"); }
void LoadLibraryA(void) { mgs2_island_forbidden("LoadLibraryA"); }
void LoadResource(void) { mgs2_island_forbidden("LoadResource"); }
void LockResource(void) { mgs2_island_forbidden("LockResource"); }
void MapWindowPoints(void) { mgs2_island_forbidden("MapWindowPoints"); }
void MonitorFromWindow(void) { mgs2_island_forbidden("MonitorFromWindow"); }
void MoveWindow(void) { mgs2_island_forbidden("MoveWindow"); }
void NtDelayExecution(void) { mgs2_island_forbidden("NtDelayExecution"); }
void NtWaitForSingleObject(void) { mgs2_island_forbidden("NtWaitForSingleObject"); }
void QueryPerformanceCounter(void) { mgs2_island_forbidden("QueryPerformanceCounter"); }
void QueryPerformanceFrequency(void) { mgs2_island_forbidden("QueryPerformanceFrequency"); }
void RegCloseKey(void) { mgs2_island_forbidden("RegCloseKey"); }
void RegOpenKeyA(void) { mgs2_island_forbidden("RegOpenKeyA"); }
void RegQueryValueExA(void) { mgs2_island_forbidden("RegQueryValueExA"); }
void RegisterClassA(void) { mgs2_island_forbidden("RegisterClassA"); }
void ReleaseDC(void) { mgs2_island_forbidden("ReleaseDC"); }
void RtlIsCriticalSectionLockedByThread(void) { mgs2_island_forbidden("RtlIsCriticalSectionLockedByThread"); }
void ScreenToClient(void) { mgs2_island_forbidden("ScreenToClient"); }
void SelectObject(void) { mgs2_island_forbidden("SelectObject"); }
void SetCursor(void) { mgs2_island_forbidden("SetCursor"); }
void SetCursorPos(void) { mgs2_island_forbidden("SetCursorPos"); }
void SetDIBColorTable(void) { mgs2_island_forbidden("SetDIBColorTable"); }
void SetDeviceGammaRamp(void) { mgs2_island_forbidden("SetDeviceGammaRamp"); }
void SetEvent(void) { mgs2_island_forbidden("SetEvent"); }
void SetPixelFormat(void) { mgs2_island_forbidden("SetPixelFormat"); }
void SetThreadDescription(void) { mgs2_island_forbidden("SetThreadDescription"); }
void SetTimer(void) { mgs2_island_forbidden("SetTimer"); }
void SetWindowLongA(void) { mgs2_island_forbidden("SetWindowLongA"); }
void SetWindowLongW(void) { mgs2_island_forbidden("SetWindowLongW"); }
void SetWindowPos(void) { mgs2_island_forbidden("SetWindowPos"); }
void SetWindowsHookExW(void) { mgs2_island_forbidden("SetWindowsHookExW"); }
void ShowWindow(void) { mgs2_island_forbidden("ShowWindow"); }
void SizeofResource(void) { mgs2_island_forbidden("SizeofResource"); }
void StretchBlt(void) { mgs2_island_forbidden("StretchBlt"); }
void SystemParametersInfoW(void) { mgs2_island_forbidden("SystemParametersInfoW"); }
void TlsAlloc(void) { mgs2_island_forbidden("TlsAlloc"); }
void TlsFree(void) { mgs2_island_forbidden("TlsFree"); }
void UnhookWindowsHookEx(void) { mgs2_island_forbidden("UnhookWindowsHookEx"); }
void UnregisterClassA(void) { mgs2_island_forbidden("UnregisterClassA"); }
void WaitForSingleObject(void) { mgs2_island_forbidden("WaitForSingleObject"); }
void __stdio_common_vsscanf(void) { mgs2_island_forbidden("__stdio_common_vsscanf"); }
void _putenv(void) { mgs2_island_forbidden("_putenv"); }
void _recalloc(void) { mgs2_island_forbidden("_recalloc"); }
void _stricmp(void) { mgs2_island_forbidden("_stricmp"); }
void glDisable(void) { mgs2_island_forbidden("glDisable"); }
void glEnable(void) { mgs2_island_forbidden("glEnable"); }
void lstrcmpiW(void) { mgs2_island_forbidden("lstrcmpiW"); }
void vkd3d_shader_build_varying_map(void) { mgs2_island_forbidden("vkd3d_shader_build_varying_map"); }
void vkd3d_shader_compile(void) { mgs2_island_forbidden("vkd3d_shader_compile"); }
void vkd3d_shader_free_dxbc(void) { mgs2_island_forbidden("vkd3d_shader_free_dxbc"); }
void vkd3d_shader_free_messages(void) { mgs2_island_forbidden("vkd3d_shader_free_messages"); }
void vkd3d_shader_free_scan_descriptor_info(void) { mgs2_island_forbidden("vkd3d_shader_free_scan_descriptor_info"); }
void vkd3d_shader_free_scan_signature_info(void) { mgs2_island_forbidden("vkd3d_shader_free_scan_signature_info"); }
void vkd3d_shader_free_shader_code(void) { mgs2_island_forbidden("vkd3d_shader_free_shader_code"); }
void vkd3d_shader_parse_dxbc(void) { mgs2_island_forbidden("vkd3d_shader_parse_dxbc"); }
void vkd3d_shader_scan(void) { mgs2_island_forbidden("vkd3d_shader_scan"); }
void vkd3d_utils_set_log_callback(void) { mgs2_island_forbidden("vkd3d_utils_set_log_callback"); }
