export type SET_GLOBALS_EVENT_TYPE = "openai:set_globals";

export type SetGlobalsEvent = CustomEvent<{
  globals: Partial<OpenAiGlobals>;
}>;

export type ToolContent =
  | { type: "text"; text: string }
  | { type: string; [k: string]: unknown };

export type ToolResult<TStructured = any> = {
  structuredContent?: TStructured;
  content?: ToolContent[];
  isError?: boolean;
  _meta?: Record<string, unknown>;
};

export type OpenAiGlobals = {
  toolInput?: any;
  toolOutput?: any;
  toolResponseMetadata?: any;
  widgetState?: any;
  theme?: "light" | "dark";
  displayMode?: "inline" | "fullscreen" | "pip";
  maxHeight?: number;
  userAgent?: any;
  locale?: string;
  setWidgetState?: (state: any) => void;
  callTool?: (name: string, args?: any) => Promise<ToolResult>;
  sendFollowUpMessage?: (args: { prompt: string }) => Promise<void> | void;
  requestDisplayMode?: (args: { mode: "inline" | "fullscreen" | "pip" }) => Promise<{ mode: "inline" | "fullscreen" | "pip" }> | any;
};

declare global {
  interface Window {
    openai?: OpenAiGlobals;
  }
}


