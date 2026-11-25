import { forwardRef } from "react";
import type { ComponentPropsWithoutRef } from "react";

// Server-safe, presentational JSX: no hooks, globals or CSS side-effect imports.
// The consuming application imports @syntyr/css/core.css once in its root.
function classes(...names: Array<string | undefined | false>) {
  return names.filter(Boolean).join(" ");
}

export type SyntyrRootProps = ComponentPropsWithoutRef<"div"> & {
  theme?: string;
};
export const SyntyrRoot = forwardRef<HTMLDivElement, SyntyrRootProps>(
  function SyntyrRoot({ theme = "studio", className, ...props }, ref) {
    return <div {...props} ref={ref} className={classes("syn-root", className)} data-syn-theme={theme} />;
  },
);

export type ButtonProps = ComponentPropsWithoutRef<"button"> & {
  variant?: "primary" | "outline" | "ghost" | "danger";
  size?: "small";
};
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  function Button({ variant, size, className, type = "button", ...props }, ref) {
    return (
      <button {...props} ref={ref} type={type}
        className={classes("syn-button", variant && "syn-button--" + variant,
          size && "syn-button--" + size, className)} />
    );
  },
);

export type CardProps = ComponentPropsWithoutRef<"article"> & {
  elevated?: boolean;
};
export const Card = forwardRef<HTMLElement, CardProps>(
  function Card({ elevated, className, ...props }, ref) {
    return <article {...props} ref={ref}
      className={classes("syn-panel", elevated && "syn-panel--raised", className)} />;
  },
);

export type BadgeProps = ComponentPropsWithoutRef<"span"> & {
  accent?: boolean;
};
export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  function Badge({ accent, className, ...props }, ref) {
    return <span {...props} ref={ref}
      className={classes("syn-badge", accent && "syn-badge--accent", className)} />;
  },
);

export type InputProps = ComponentPropsWithoutRef<"input">;
export const Input = forwardRef<HTMLInputElement, InputProps>(
  function Input({ className, ...props }, ref) {
    return <input {...props} ref={ref} className={classes("syn-input", className)} />;
  },
);

export type SelectProps = ComponentPropsWithoutRef<"select">;
export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  function Select({ className, ...props }, ref) {
    return <select {...props} ref={ref} className={classes("syn-select", className)} />;
  },
);

export type TextareaProps = ComponentPropsWithoutRef<"textarea">;
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  function Textarea({ className, ...props }, ref) {
    return <textarea {...props} ref={ref} className={classes("syn-textarea", className)} />;
  },
);
