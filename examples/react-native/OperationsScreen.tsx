/** Fictional, copy-owned SaaS workspace. No network, persistence or authentication. */
import React, { useMemo, useState } from "react";
import { FlatList, KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from "react-native";
import { createSyntyrNativeStyles, type SyntyrNativeInsets } from "../../integrations/react-native/styles";
import { syntyrMobileTokens, type SyntyrMobileTheme } from "../../integrations/react-native/tokens";
import {
  NativeAction, NativeField, NativeMetric, NativeRecord, NativeState, NativeStatus, NativeTabs,
  type SyntyrStatusTone,
} from "../../integrations/react-native/recipes";

type Tab = "overview" | "clients" | "settings";
const tabs = [
  { id: "overview", label: "Overview" },
  { id: "clients", label: "Clients" },
  { id: "settings", label: "Settings" },
] as const;
const records: ReadonlyArray<{
  id: string; title: string; description: string; status: string; tone: SyntyrStatusTone;
}> = [
  { id: "north", title: "Northstar Studio", description: "Creative services", status: "Active", tone: "success" },
  { id: "harbor", title: "Harbor Retail", description: "Retail operations", status: "Needs review", tone: "warning" },
  { id: "mesa", title: "Mesa Works", description: "Field operations", status: "Follow-up due", tone: "danger" },
];

export default function OperationsScreen({ theme, insets, onBack }: { theme: SyntyrMobileTheme; insets?: SyntyrNativeInsets; onBack: () => void }) {
  const styles = useMemo(() => StyleSheet.create(createSyntyrNativeStyles(theme, Platform.OS, insets)), [theme, insets]);
  const [tab, setTab] = useState<Tab>("overview");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [name, setName] = useState("Northstar workspace");
  const [saveAttempted, setSaveAttempted] = useState(false);
  const [saved, setSaved] = useState(false);
  const spacing = syntyrMobileTokens.spacing;
  const filtered = records.filter((record) =>
    `${record.title} ${record.description} ${record.status}`.toLowerCase().includes(query.trim().toLowerCase()),
  );
  const selectedRecord = filtered.find((record) => record.id === selected);
  const changeQuery = (next: string) => { setQuery(next); setSelected(null); };
  const save = () => {
    setSaveAttempted(true);
    setSaved(name.trim() !== "");
  };
  const changeName = (next: string) => {
    setName(next);
    setSaved(false);
  };
  const error = saveAttempted && !name.trim() ? "Enter a workspace name." : undefined;
  const header = (
      <View style={styles.stack}>
        <NativeAction styles={styles} label="Back to basic recipes" secondary onPress={onBack} />
        <Text accessibilityRole="header" style={styles.metricValue}>Operations workspace</Text>
        <Text style={styles.body}>Illustrative records · local preview only</Text>
        <NativeTabs<Tab> styles={styles} tabs={tabs} selected={tab} onSelect={setTab} />
      </View>
  );
  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      style={styles.screen}
    >
      {tab === "clients" ? (
        <FlatList
          style={{ flex: 1 }}
          contentInsetAdjustmentBehavior={insets ? "never" : "automatic"}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ gap: spacing["2"], paddingVertical: spacing["3"] }}
          data={filtered}
          keyExtractor={(record) => record.id}
          ListHeaderComponent={
            <View style={styles.stack}>
              {header}
              <NativeField styles={styles} label="Search clients" value={query} onChangeText={changeQuery}
                placeholder="Name, sector or status" autoCapitalize="none" />
              <Text accessibilityLiveRegion="polite" style={styles.body}>{filtered.length} matching clients</Text>
              {selectedRecord && (
                <View style={[styles.panel, styles.stack]}>
                  <Text accessibilityRole="header" style={styles.heading}>Selected client: {selectedRecord.title}</Text>
                  <NativeStatus styles={styles} label={selectedRecord.status} tone={selectedRecord.tone} />
                </View>
              )}
            </View>
          }
          ListEmptyComponent={<NativeState styles={styles} kind="empty" title="No matching clients"
            description="Try a different name or clear the search."
            action={{ label: "Clear search", onPress: () => changeQuery("") }} />}
          renderItem={({ item }) => <NativeRecord styles={styles} {...item} selected={selected === item.id}
            onPress={() => setSelected(item.id)} />}
        />
      ) : (
        <ScrollView
          style={{ flex: 1 }}
          contentInsetAdjustmentBehavior={insets ? "never" : "automatic"}
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ gap: spacing["2"], paddingVertical: spacing["3"] }}
        >
          {header}
          {tab === "overview" ? <>
            <Text accessibilityRole="header" style={styles.heading}>This quarter</Text>
            <View style={styles.metricGrid}>
              <NativeMetric styles={styles} label="Booked revenue" value="$42k" detail="Sample total" />
              <NativeMetric styles={styles} label="Active clients" value="18" detail="Sample accounts" />
              <NativeMetric styles={styles} label="Open proposals" value="7" detail="Sample pipeline" />
              <NativeMetric styles={styles} label="Tasks due" value="4" detail="Sample workload" />
            </View>
            <View style={[styles.panel, styles.stack]}>
              <Text accessibilityRole="header" style={styles.heading}>Client follow-up</Text>
              <NativeStatus styles={styles} label="Needs review" tone="warning" />
              <Text style={styles.body}>One illustrative account needs a review.</Text>
              <NativeAction styles={styles} label="Review clients" onPress={() => setTab("clients")} />
            </View>
          </> : <>
            <View style={[styles.panel, styles.stack]}>
              <Text accessibilityRole="header" style={styles.heading}>Workspace details</Text>
              <NativeField styles={styles} label="Workspace name" value={name} onChangeText={changeName}
                error={error} hint="Changes are not sent to a server." />
              <NativeAction styles={styles} label="Save preview" onPress={save} />
              {saved && <Text accessibilityLiveRegion="polite" style={[styles.body, styles.statusSuccess]}>Preview saved locally.</Text>}
            </View>
          </>}
        </ScrollView>
      )}
    </KeyboardAvoidingView>
  );
}
