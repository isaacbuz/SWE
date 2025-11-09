/**
 * Google Workspace API Tool Wrapper
 * 
 * Provides secure wrappers around Google Workspace APIs (Sheets, Drive, etc.).
 */
import { google } from 'googleapis';
import { CredentialVault, Credentials } from '../types/CredentialVault';
import { RateLimiter } from '../utils/RateLimiter';

/**
 * Google Workspace Tool Wrapper
 * 
 * Provides secure wrappers around Google Workspace API operations.
 */
export class GoogleWorkspaceToolWrapper {
  private auth: any = null;
  private rateLimiter: RateLimiter;

  constructor(private credentialVault: CredentialVault) {
    // Google API rate limits vary by service
    this.rateLimiter = new RateLimiter({
      maxRequests: 1000,
      windowMs: 60 * 1000, // 1 minute
    });
  }

  /**
   * Initialize Google API client with credentials
   */
  private async initialize(): Promise<void> {
    if (this.auth) {
      return;
    }

    const credentials = await this.credentialVault.getCredentials('google-workspace');
    if (!credentials || !credentials.token) {
      throw new Error('Google Workspace credentials not found');
    }

    // Initialize OAuth2 client
    const oauth2Client = new google.auth.OAuth2(
      credentials.clientId,
      credentials.clientSecret,
      credentials.redirectUri
    );

    oauth2Client.setCredentials({
      access_token: credentials.token,
      refresh_token: credentials.refreshToken,
    });

    this.auth = oauth2Client;
  }

  // ========== Google Sheets Operations ==========

  /**
   * Read data from a Google Sheet
   */
  async readSheet(
    spreadsheetId: string,
    range: string
  ): Promise<any[][]> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-sheets');

    const sheets = google.sheets({ version: 'v4', auth: this.auth });
    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range,
    });

    return response.data.values || [];
  }

  /**
   * Write data to a Google Sheet
   */
  async writeSheet(
    spreadsheetId: string,
    range: string,
    values: any[][]
  ): Promise<void> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-sheets');

    const sheets = google.sheets({ version: 'v4', auth: this.auth });
    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range,
      valueInputOption: 'RAW',
      requestBody: {
        values,
      },
    });
  }

  /**
   * Create a new Google Sheet
   */
  async createSheet(title: string): Promise<{ id: string; url: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-sheets');

    const sheets = google.sheets({ version: 'v4', auth: this.auth });
    const response = await sheets.spreadsheets.create({
      requestBody: {
        properties: {
          title,
        },
      },
    });

    return {
      id: response.data.spreadsheetId!,
      url: response.data.spreadsheetUrl!,
    };
  }

  /**
   * Get sheet metadata
   */
  async getSheetMetadata(spreadsheetId: string): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-sheets');

    const sheets = google.sheets({ version: 'v4', auth: this.auth });
    const response = await sheets.spreadsheets.get({
      spreadsheetId,
    });

    return {
      id: response.data.spreadsheetId,
      title: response.data.properties?.title,
      sheets: response.data.sheets?.map((s: any) => ({
        id: s.properties.sheetId,
        title: s.properties.title,
      })),
    };
  }

  // ========== Google Drive Operations ==========

  /**
   * List files in Google Drive
   */
  async listFiles(options?: {
    query?: string;
    pageSize?: number;
    pageToken?: string;
  }): Promise<{ files: any[]; nextPageToken?: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-drive');

    const drive = google.drive({ version: 'v3', auth: this.auth });
    const response = await drive.files.list({
      q: options?.query,
      pageSize: options?.pageSize || 10,
      pageToken: options?.pageToken,
      fields: 'nextPageToken, files(id, name, mimeType, createdTime, modifiedTime, webViewLink)',
    });

    return {
      files: response.data.files || [],
      nextPageToken: response.data.nextPageToken || undefined,
    };
  }

  /**
   * Get file metadata
   */
  async getFile(fileId: string): Promise<any> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-drive');

    const drive = google.drive({ version: 'v3', auth: this.auth });
    const response = await drive.files.get({
      fileId,
      fields: 'id, name, mimeType, createdTime, modifiedTime, webViewLink, size',
    });

    return response.data;
  }

  /**
   * Download file content
   */
  async downloadFile(fileId: string): Promise<Buffer> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-drive');

    const drive = google.drive({ version: 'v3', auth: this.auth });
    const response = await drive.files.get(
      {
        fileId,
        alt: 'media',
      },
      { responseType: 'arraybuffer' }
    );

    return Buffer.from(response.data as ArrayBuffer);
  }

  /**
   * Upload file to Google Drive
   */
  async uploadFile(
    name: string,
    mimeType: string,
    content: Buffer,
    parentFolderId?: string
  ): Promise<{ id: string; webViewLink: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-drive');

    const drive = google.drive({ version: 'v3', auth: this.auth });
    const response = await drive.files.create({
      requestBody: {
        name,
        mimeType,
        parents: parentFolderId ? [parentFolderId] : undefined,
      },
      media: {
        mimeType,
        body: content,
      },
      fields: 'id, webViewLink',
    });

    return {
      id: response.data.id!,
      webViewLink: response.data.webViewLink!,
    };
  }

  /**
   * Create a folder in Google Drive
   */
  async createFolder(
    name: string,
    parentFolderId?: string
  ): Promise<{ id: string; webViewLink: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-drive');

    const drive = google.drive({ version: 'v3', auth: this.auth });
    const response = await drive.files.create({
      requestBody: {
        name,
        mimeType: 'application/vnd.google-apps.folder',
        parents: parentFolderId ? [parentFolderId] : undefined,
      },
      fields: 'id, webViewLink',
    });

    return {
      id: response.data.id!,
      webViewLink: response.data.webViewLink!,
    };
  }

  // ========== Google Docs Operations ==========

  /**
   * Create a Google Doc
   */
  async createDoc(title: string): Promise<{ id: string; url: string }> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-docs');

    const docs = google.docs({ version: 'v1', auth: this.auth });
    const drive = google.drive({ version: 'v3', auth: this.auth });

    // Create document via Drive API
    const response = await drive.files.create({
      requestBody: {
        name: title,
        mimeType: 'application/vnd.google-apps.document',
      },
      fields: 'id, webViewLink',
    });

    return {
      id: response.data.id!,
      url: response.data.webViewLink!,
    };
  }

  /**
   * Read Google Doc content
   */
  async readDoc(documentId: string): Promise<string> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-docs');

    const docs = google.docs({ version: 'v1', auth: this.auth });
    const response = await docs.documents.get({
      documentId,
    });

    // Extract text content
    const content = response.data.body?.content || [];
    let text = '';

    for (const element of content) {
      if (element.paragraph) {
        for (const element of element.paragraph.elements || []) {
          if (element.textRun) {
            text += element.textRun.content || '';
          }
        }
      }
    }

    return text;
  }

  /**
   * Update Google Doc content
   */
  async updateDoc(
    documentId: string,
    text: string
  ): Promise<void> {
    await this.initialize();
    await this.rateLimiter.checkLimit('google-docs');

    const docs = google.docs({ version: 'v1', auth: this.auth });

    // Get document to find end index
    const doc = await docs.documents.get({ documentId });
    const endIndex = doc.data.body?.content?.[doc.data.body.content.length - 1]?.endIndex || 1;

    // Insert text at the end
    await docs.documents.batchUpdate({
      documentId,
      requestBody: {
        requests: [
          {
            insertText: {
              location: {
                index: endIndex - 1,
              },
              text,
            },
          },
        ],
      },
    });
  }
}

