# CLAUDE.md — OpenJarvis App (Flutter)

## Architecture

```
app/
  lib/
    main.dart                          # OmniAgentApp entry point
    src/
      models/                          # DeviceRecord, TaskRecord, TaskStatus
      services/                        # GatewayApi + GatewaySocket (abstract + impl)
      state/task_controller.dart       # ChangeNotifier, ConnectionStatus enum
      ui/
        home_screen.dart               # Main UI shell (all widgets)
        app_theme.dart                 # JarvisThemeTokens + JarvisAppTheme
        helpers.dart                   # Shared pure functions
        components/                    # Extracted reusable widgets (GlassCard, etc.)
        chat/                          # Extracted chat widgets (ComposerBar, etc.)
        sidebar/                       # Extracted sidebar widgets (ThreadRail, etc.)
        app_bar.dart                   # Extracted app bar
        settings_sheet.dart            # Extracted settings bottom sheet
        workspace_summary.dart         # Extracted workspace summary
        jarvis_app_shell.dart          # Alternative shell (extracted version)
  test/
    helpers/test_fakes.dart            # FakeGatewayApi, FakeGatewaySocket, pumpApp
    task_controller_test.dart          # Unit tests (inline fakes)
    widget_test.dart                   # Widget tests (inline fakes, pumpFrames)
    ui/                                # Extracted component tests
```

## Key Conventions

- **Language**: All user-facing strings are Chinese (简体中文)
- **State management**: Manual `ChangeNotifier` via `TaskController` — no external packages
- **Test doubles**: Abstract service interfaces (`GatewayApi`, `GatewaySocket`) with fake implementations in tests
- **Animations**: Use `pumpFrames()` (not `pumpAndSettle()`) in tests — app has repeating animations
- **Theme**: `JarvisThemeTokens` ThemeExtension with 27 semantic colors; access via `JarvisThemeTokens.of(context)`
- **Keys**: Widget tests rely on specific Keys (e.g., `chatSendButton`, `chatComposerField`, `appBarMenuButton`) — preserve them

## Commands

```bash
cd app && flutter test          # Run all tests (must pass before committing)
cd app && flutter analyze       # Static analysis (zero warnings required)
```

## TDD Workflow

Per `AGENTS.md`:
1. Write failing test first
2. Implement minimum code to pass
3. Run `flutter test` to verify
4. Ensure all three modules (gateway, client, app) protocol contracts still hold

## Models

- `TaskStatus` enum: 9 states (pendingDispatch → running → awaitingApproval → approved/rejected → resuming → completed/failed)
- `TaskRecord`: taskId, deviceId, instruction, status, checkpointId, command, reason, result, error, logs
- `DeviceRecord`: deviceId, connected

## API Endpoints

- `POST /auth/login` → JWT token
- `GET /tasks/pending_approvals` → List of awaiting-approval tasks
- `GET /devices` → List of connected devices
- `POST /tasks` → Create task (deviceId + instruction)
- `POST /tasks/{id}/decision` → Approve/reject
- `WS /ws/app?token=...` → Real-time events (TASK_SNAPSHOT, TASK_LOG)
