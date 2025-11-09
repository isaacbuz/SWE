import { describe, it, expect, beforeEach } from 'vitest';
import { ToolRegistry } from './ToolRegistry';
import { ToolSpec } from '../types/ToolSpec';

describe('ToolRegistry', () => {
  let registry: ToolRegistry;

  beforeEach(() => {
    registry = new ToolRegistry();
  });

  describe('constructor', () => {
    it('should create registry with default options', () => {
      const reg = new ToolRegistry();
      expect(reg.getToolCount()).toBe(0);
    });

    it('should create registry with custom options', () => {
      const reg = new ToolRegistry({
        validateOnLoad: false,
        allowDuplicates: true,
      });
      expect(reg.getToolCount()).toBe(0);
    });
  });

  describe('getToolSpecs', () => {
    it('should return empty array initially', () => {
      expect(registry.getToolSpecs()).toEqual([]);
    });

    it('should return all registered tools', () => {
      // Mock tools would be added via loadSpecs
      // For now, test empty state
      expect(registry.getToolSpecs().length).toBe(0);
    });
  });

  describe('getToolByName', () => {
    it('should return undefined for non-existent tool', () => {
      expect(registry.getToolByName('nonexistent')).toBeUndefined();
    });
  });

  describe('hasTool', () => {
    it('should return false for non-existent tool', () => {
      expect(registry.hasTool('nonexistent')).toBe(false);
    });
  });

  describe('getToolCount', () => {
    it('should return 0 initially', () => {
      expect(registry.getToolCount()).toBe(0);
    });
  });

  describe('clear', () => {
    it('should clear all tools', () => {
      registry.clear();
      expect(registry.getToolCount()).toBe(0);
      expect(registry.getLoadedSpecs().length).toBe(0);
    });
  });

  describe('getLoadedSpecs', () => {
    it('should return empty array initially', () => {
      expect(registry.getLoadedSpecs()).toEqual([]);
    });
  });
});

