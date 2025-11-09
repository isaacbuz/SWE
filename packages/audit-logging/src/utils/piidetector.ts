/**
 * PII Detection and Redaction
 */

import { PIIDetectionResult } from '../types';

/**
 * Patterns for common PII types
 */
const PII_PATTERNS = {
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  phone: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g,
  ssn: /\b\d{3}-\d{2}-\d{4}\b/g,
  creditCard: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
  ipAddress: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g,
};

/**
 * PII Detector
 */
export class PIIDetector {
  /**
   * Detect and redact PII from content
   */
  detectAndRedact(content: unknown): PIIDetectionResult {
    if (typeof content === 'string') {
      return this.detectInString(content);
    }

    if (typeof content === 'object' && content !== null) {
      if (Array.isArray(content)) {
        const results = content.map((item) => this.detectAndRedact(item));
        const detected = results.some((r) => r.detected);
        const types = Array.from(
          new Set(results.flatMap((r) => r.types))
        );
        const redacted = results.map((r) => r.redactedContent);

        return {
          detected,
          types,
          redactedContent: redacted,
        };
      }

      // Object
      const redacted: Record<string, unknown> = {};
      const allTypes: string[] = [];
      let anyDetected = false;

      for (const [key, value] of Object.entries(content)) {
        const result = this.detectAndRedact(value);
        if (result.detected) {
          anyDetected = true;
          allTypes.push(...result.types);
        }
        redacted[key] = result.redactedContent;
      }

      return {
        detected: anyDetected,
        types: Array.from(new Set(allTypes)),
        redactedContent: redacted,
      };
    }

    // Primitive types - no PII
    return {
      detected: false,
      types: [],
      redactedContent: content,
    };
  }

  /**
   * Detect PII in string
   */
  private detectInString(text: string): PIIDetectionResult {
    const detectedTypes: string[] = [];
    let redacted = text;

    for (const [type, pattern] of Object.entries(PII_PATTERNS)) {
      if (pattern.test(text)) {
        detectedTypes.push(type);
        redacted = redacted.replace(pattern, `[${type.toUpperCase()}_REDACTED]`);
      }
    }

    return {
      detected: detectedTypes.length > 0,
      types: detectedTypes,
      redactedContent: redacted,
    };
  }
}

