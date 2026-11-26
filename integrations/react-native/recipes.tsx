/** Optional copy-owned React Native presentation. Host owns navigation and data. */
import React from "react";
import { ActivityIndicator, Pressable, Text, TextInput, View, type TextInputProps } from "react-native";
import type { createSyntyrNativeStyles } from "./styles";

export type SyntyrNativeStyles = ReturnType<typeof createSyntyrNativeStyles>;
export type SyntyrStatusTone = "neutral" | "success" | "warning" | "danger";

type Styled = { styles: SyntyrNativeStyles };

export function NativeAction({ styles, label, onPress, secondary = false, disabled = false, busy = false }: Styled & {
  label: string; onPress: () => void; secondary?: boolean; disabled?: boolean; busy?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || busy, busy }}
      disabled={disabled || busy}
      onPress={onPress}
      style={({ pressed }) => [
        styles.action,
        secondary && styles.actionSecondary,
        pressed && (secondary ? styles.actionSecondaryPressed : styles.actionPressed),
        (disabled || busy) && styles.buttonDisabled,
      ]}
    >
      <Text style={[styles.buttonLabel, secondary && styles.actionSecondaryLabel]}>{label}</Text>
    </Pressable>
  );
}

export function NativeMetric({ styles, label, value, detail }: Styled & {
  label: string; value: string; detail?: string;
}) {
  return (
    <View style={[styles.panel, styles.metricCard]}>
      <Text style={styles.body}>{label}</Text>
      <Text style={styles.metricValue}>{value}</Text>
      {detail && <Text style={styles.body}>{detail}</Text>}
    </View>
  );
}

export function NativeStatus({ styles, label, tone = "neutral" }: Styled & {
  label: string; tone?: SyntyrStatusTone;
}) {
  const toneStyle = {
    neutral: undefined,
    success: styles.statusSuccess,
    warning: styles.statusWarning,
    danger: styles.statusDanger,
  }[tone];
  return (
    <View style={styles.badge}>
      <Text style={[styles.badgeLabel, toneStyle]}>{label}</Text>
    </View>
  );
}

/** A visible label and error message; host owns validation and focus recovery. */
export function NativeField({ styles, label, value, onChangeText, error, hint, editable = true,
  placeholder, keyboardType, autoCapitalize, autoComplete }: Styled & {
  label: string; value: string; onChangeText: (value: string) => void; error?: string; hint?: string;
  editable?: boolean; placeholder?: string; keyboardType?: TextInputProps["keyboardType"];
  autoCapitalize?: TextInputProps["autoCapitalize"]; autoComplete?: TextInputProps["autoComplete"];
}) {
  return (
    <View style={styles.stack}>
      <Text style={styles.controlLabel}>{label}</Text>
      <TextInput
        accessibilityLabel={label}
        accessibilityHint={error || hint}
        accessibilityState={{ disabled: !editable }}
        editable={editable}
        style={[styles.input, error && styles.inputError, !editable && styles.buttonDisabled]}
        placeholder={placeholder}
        placeholderTextColor={styles.body.color}
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType}
        autoCapitalize={autoCapitalize}
        autoComplete={autoComplete}
      />
      {!!error && <Text accessibilityLiveRegion="polite" style={[styles.body, styles.statusDanger]}>{error}</Text>}
      {!error && !!hint && <Text style={styles.body}>{hint}</Text>}
    </View>
  );
}

export type NativeTab<T extends string> = { id: T; label: string };

export function NativeTabs<T extends string>({ styles, tabs, selected, onSelect }: Styled & {
  tabs: ReadonlyArray<NativeTab<T>>; selected: T; onSelect: (id: T) => void;
}) {
  return (
    <View accessibilityRole="tablist" style={styles.tabStrip}>
      {tabs.map(({ id, label }) => {
        const active = selected === id;
        return (
          <Pressable
            key={id}
            accessibilityRole="tab"
            accessibilityState={{ selected: active }}
            onPress={() => onSelect(id)}
            style={[styles.tab, active && styles.tabSelected]}
          >
            <Text style={[styles.buttonLabel, !active && styles.actionSecondaryLabel]}>{label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export function NativeRecord({ styles, title, description, status, tone, onPress, selected = false }: Styled & {
  title: string; description: string; status: string; tone?: SyntyrStatusTone;
  onPress?: () => void; selected?: boolean;
}) {
  const content = <>
    <Text style={styles.controlLabel}>{title}</Text>
    <Text style={styles.body}>{description}</Text>
    <NativeStatus styles={styles} label={status} tone={tone} />
  </>;
  return onPress ? (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${title}, ${description}, ${status}`}
      accessibilityState={{ selected }}
      onPress={onPress}
      style={[styles.record, selected && styles.recordSelected]}
    >{content}</Pressable>
  ) : <View style={styles.record}>{content}</View>;
}

export function NativeState({ styles, kind, title, description, action }: Styled & {
  kind: "empty" | "error" | "loading";
  title: string; description: string; action?: { label: string; onPress: () => void };
}) {
  return (
    <View style={[styles.panel, styles.stack]}>
      {kind === "loading" && <ActivityIndicator accessibilityLabel="Loading" color={styles.action.backgroundColor} />}
      <Text accessibilityRole="header" style={[styles.heading, kind === "error" && styles.statusDanger, { marginBottom: 0 }]}>{title}</Text>
      <Text accessibilityLiveRegion="polite" style={styles.body}>{description}</Text>
      {kind !== "loading" && action && <NativeAction styles={styles} secondary {...action} />}
    </View>
  );
}

