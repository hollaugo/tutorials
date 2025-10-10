/**
 * OpenAI Apps SDK Types
 * Based on: https://developers.openai.com/apps-sdk/build/custom-ux
 */

export type Theme = "light" | "dark";
export type DisplayMode = "pip" | "inline" | "fullscreen";
export type DeviceType = "mobile" | "tablet" | "desktop" | "unknown";

export interface SafeAreaInsets {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface SafeArea {
  insets: SafeAreaInsets;
}

export interface UserAgent {
  device: { type: DeviceType };
  capabilities: {
    hover: boolean;
    touch: boolean;
  };
}

export interface CallToolResponse {
  content: Array<{
    type: string;
    text?: string;
  }>;
  isError?: boolean;
}

export interface OpenAiGlobals<
  ToolInput = any,
  ToolOutput = any,
  ToolResponseMetadata = any,
  WidgetState = any
> {
  theme: Theme;
  userAgent: UserAgent;
  locale: string;
  maxHeight: number;
  displayMode: DisplayMode;
  safeArea: SafeArea;
  toolInput: ToolInput;
  toolOutput: ToolOutput | null;
  toolResponseMetadata: ToolResponseMetadata | null;
  widgetState: WidgetState | null;
}

export interface OpenAiAPI<WidgetState = any> {
  callTool: (name: string, args: Record<string, unknown>) => Promise<CallToolResponse>;
  sendFollowUpMessage: (args: { prompt: string }) => Promise<void>;
  openExternal: (payload: { href: string }) => void;
  requestDisplayMode: (args: { mode: DisplayMode }) => Promise<{ mode: DisplayMode }>;
  setWidgetState: (state: WidgetState) => Promise<void>;
}

export const SET_GLOBALS_EVENT_TYPE = "openai:set_globals";

export class SetGlobalsEvent extends CustomEvent<{
  globals: Partial<OpenAiGlobals>;
}> {
  readonly type = SET_GLOBALS_EVENT_TYPE;
}

declare global {
  interface Window {
    openai: OpenAiAPI & OpenAiGlobals;
  }

  interface WindowEventMap {
    [SET_GLOBALS_EVENT_TYPE]: SetGlobalsEvent;
  }
}

// FPL-specific types
export interface PlayerData {
  name: string;
  team: string;
  position: string;
  price: number;
  points: number;
  goals: number;
  assists: number;
  form: number;
  form_indicator?: string;
  selected_by?: number;
}

export interface PlayerDetailData {
  name: string;
  team: string;
  position: string;
  price: number;
  total_points: number;
  form: string;
  selected_by: string;
  goals: number;
  assists: number;
  clean_sheets: number;
  fixtures?: Array<{
    gameweek: number;
    opponent: string;
    difficulty: number;
  }>;
}

export interface PlayerListWidgetState {
  favorites: number[];
  filters?: {
    position?: string;
    maxPrice?: number;
  };
}

export interface PlayerComparisonWidgetState {
  favorites: number[];
}

