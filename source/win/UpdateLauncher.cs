using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;

internal static class UpdateLauncher
{
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int MessageBoxW(IntPtr hWnd, string text, string caption, uint type);

    private static string FindRoot(string startDir)
    {
        string dir = Path.GetFullPath(startDir.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar));
        for (int i = 0; i < 3 && !string.IsNullOrEmpty(dir); i++)
        {
            if (File.Exists(Path.Combine(dir, "tools", "bq-update.exe")) ||
                File.Exists(Path.Combine(dir, "tools", "bq_update.py")))
            {
                return dir;
            }
            DirectoryInfo parent = Directory.GetParent(dir);
            dir = parent != null ? parent.FullName : null;
        }
        return null;
    }

    [STAThread]
    private static int Main()
    {
        string root = FindRoot(AppDomain.CurrentDomain.BaseDirectory);
        if (root == null)
        {
            MessageBoxW(
                IntPtr.Zero,
                "Could not find tools\\bq-update.exe next to Update.exe.\n\n" +
                "Unzip the whole BAKOQUAKE folder and run Update.exe from inside it.",
                "BAKOQUAKE Updater",
                0x10
            );
            return 1;
        }

        string exePath = Path.Combine(root, "tools", "bq-update.exe");
        string pyPath = Path.Combine(root, "tools", "bq_update.py");
        string rootArg = root.TrimEnd('\\');

        try
        {
            var psi = new ProcessStartInfo
            {
                WorkingDirectory = root,
                UseShellExecute = false,
                CreateNoWindow = true,
            };

            if (File.Exists(exePath))
            {
                psi.FileName = exePath;
                psi.Arguments = "--standalone --root \"" + rootArg + "\"";
            }
            else
            {
                psi.FileName = "pythonw";
                psi.Arguments = "\"" + pyPath + "\" --standalone --root \"" + rootArg + "\"";
            }

            try
            {
                Process.Start(psi);
            }
            catch (Exception)
            {
                if (!File.Exists(exePath) && psi.FileName == "pythonw")
                {
                    psi.FileName = "python";
                    Process.Start(psi);
                }
                else
                {
                    throw;
                }
            }
            return 0;
        }
        catch (Exception ex)
        {
            MessageBoxW(
                IntPtr.Zero,
                "Could not launch the BAKOQUAKE updater:\n\n" + ex.Message,
                "BAKOQUAKE Updater",
                0x10
            );
            return 1;
        }
    }
}
