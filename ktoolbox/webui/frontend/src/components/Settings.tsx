import React, { useState, useEffect } from 'react';
import { ktoolboxApi } from '../utils/api';

export const Settings: React.FC = () => {
  const [envContent, setEnvContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [version, setVersion] = useState<string>('');
  const [siteVersion, setSiteVersion] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [envRes, versionRes, siteVersionRes] = await Promise.all([
          ktoolboxApi.getExampleEnv(),
          ktoolboxApi.getVersion(),
          ktoolboxApi.getSiteVersion(),
        ]);
        
        setEnvContent(envRes.env_content);
        setVersion(versionRes.version);
        setSiteVersion(siteVersionRes.site_version);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch settings');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const downloadEnvFile = () => {
    const blob = new Blob([envContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'example.env';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-b-2 border-primary rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Configuration and system information
        </p>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* System Information */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold mb-4">System Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">KToolBox Version</label>
            <div className="text-lg font-medium text-primary">{version}</div>
          </div>
          <div>
            <label className="label">Site Version</label>
            <div className="text-lg font-medium text-muted-foreground">{siteVersion}</div>
          </div>
        </div>
      </div>

      {/* Configuration */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Configuration Template</h2>
          <button
            onClick={downloadEnvFile}
            className="btn btn-primary px-4 py-2"
          >
            📄 Download .env Template
          </button>
        </div>
        
        <p className="text-muted-foreground mb-4">
          Below is an example configuration file with all available options. 
          You can download this template and modify it according to your needs.
        </p>

        <div className="bg-muted p-4 rounded-lg">
          <pre className="text-sm overflow-auto max-h-96 whitespace-pre-wrap">
            {envContent}
          </pre>
        </div>

        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">📝 Configuration Notes</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Copy the downloaded template to your KToolBox directory</li>
            <li>• Rename it to <code className="bg-blue-100 px-1 rounded">prod.env</code> or <code className="bg-blue-100 px-1 rounded">.env</code></li>
            <li>• Uncomment and modify the values you want to change</li>
            <li>• Restart KToolBox WebUI to apply the changes</li>
          </ul>
        </div>
      </div>

      {/* Help & Documentation */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold mb-4">Help & Documentation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href="https://ktoolbox.readthedocs.io/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">📚</div>
            <div>
              <div className="font-medium">Documentation</div>
              <div className="text-sm text-muted-foreground">Complete user guide and API reference</div>
            </div>
          </a>

          <a
            href="https://github.com/Ljzd-PRO/KToolBox"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">🐙</div>
            <div>
              <div className="font-medium">GitHub Repository</div>
              <div className="text-sm text-muted-foreground">Source code and issue tracker</div>
            </div>
          </a>

          <a
            href="https://github.com/Ljzd-PRO/KToolBox/releases"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">🎁</div>
            <div>
              <div className="font-medium">Releases</div>
              <div className="text-sm text-muted-foreground">Download latest version</div>
            </div>
          </a>

          <a
            href="https://github.com/Ljzd-PRO/KToolBox/issues"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-3 p-4 border rounded-lg hover:bg-accent transition-colors"
          >
            <div className="text-2xl">🐛</div>
            <div>
              <div className="font-medium">Report Issues</div>
              <div className="text-sm text-muted-foreground">Bug reports and feature requests</div>
            </div>
          </a>
        </div>
      </div>

      {/* About */}
      <div className="card p-6">
        <h2 className="text-xl font-semibold mb-4">About KToolBox</h2>
        <p className="text-muted-foreground leading-relaxed">
          KToolBox is a useful CLI tool for downloading posts from Kemono.cr / .su / .party. 
          It supports multi-file concurrent downloads, automatic retry on failures, 
          custom file naming, and much more. This WebUI provides a user-friendly interface 
          to access all the powerful features of KToolBox through your web browser.
        </p>
      </div>
    </div>
  );
};