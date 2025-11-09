/**
 * GitHub Webhook Handler
 * 
 * Handles incoming GitHub webhook events securely.
 */
import { IncomingMessage } from 'http';
import crypto from 'crypto';

export interface WebhookEvent {
  id: string;
  name: string;
  payload: any;
  timestamp: string;
}

export interface WebhookHandler {
  (event: WebhookEvent): Promise<void>;
}

/**
 * GitHub Webhook Handler
 * 
 * Validates webhook signatures and routes events to handlers.
 */
export class GitHubWebhookHandler {
  private secret: string;
  private handlers: Map<string, WebhookHandler[]> = new Map();

  constructor(secret: string) {
    if (!secret) {
      throw new Error('Webhook secret is required');
    }
    this.secret = secret;
  }

  /**
   * Register a handler for a specific event type
   */
  on(eventName: string, handler: WebhookHandler): void {
    if (!this.handlers.has(eventName)) {
      this.handlers.set(eventName, []);
    }
    this.handlers.get(eventName)!.push(handler);
  }

  /**
   * Verify webhook signature
   */
  private verifySignature(payload: string, signature: string): boolean {
    if (!signature) {
      return false;
    }

    const hmac = crypto.createHmac('sha256', this.secret);
    const digest = 'sha256=' + hmac.update(payload).digest('hex');
    
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(digest)
    );
  }

  /**
   * Parse webhook payload
   */
  private parsePayload(body: string): any {
    try {
      return JSON.parse(body);
    } catch (error) {
      throw new Error('Invalid JSON payload');
    }
  }

  /**
   * Handle incoming webhook request
   */
  async handle(
    req: IncomingMessage,
    body: string,
    signature: string
  ): Promise<void> {
    // Verify signature
    if (!this.verifySignature(body, signature)) {
      throw new Error('Invalid webhook signature');
    }

    // Parse payload
    const payload = this.parsePayload(body);
    const eventName = req.headers['x-github-event'] as string;
    const deliveryId = req.headers['x-github-delivery'] as string;

    if (!eventName || !deliveryId) {
      throw new Error('Missing required webhook headers');
    }

    // Create event object
    const event: WebhookEvent = {
      id: deliveryId,
      name: eventName,
      payload,
      timestamp: new Date().toISOString(),
    };

    // Route to handlers
    const handlers = this.handlers.get(eventName) || [];
    const allHandlers = this.handlers.get('*') || []; // Wildcard handlers

    // Execute all handlers
    await Promise.all([
      ...handlers.map((h) => h(event)),
      ...allHandlers.map((h) => h(event)),
    ]);
  }

  /**
   * Express.js middleware
   */
  middleware() {
    return async (req: any, res: any, next: any) => {
      if (req.method !== 'POST') {
        return next();
      }

      try {
        const signature = req.headers['x-hub-signature-256'] as string;
        const body = JSON.stringify(req.body);

        await this.handle(req, body, signature);

        res.status(200).json({ received: true });
      } catch (error: any) {
        res.status(400).json({ error: error.message });
      }
    };
  }

  /**
   * Fastify plugin
   */
  fastifyPlugin() {
    return async (fastify: any) => {
      fastify.post('/webhooks/github', async (request: any, reply: any) => {
        try {
          const signature = request.headers['x-hub-signature-256'] as string;
          const body = JSON.stringify(request.body);

          await this.handle(request.raw, body, signature);

          return { received: true };
        } catch (error: any) {
          reply.code(400).send({ error: error.message });
        }
      });
    };
  }
}

