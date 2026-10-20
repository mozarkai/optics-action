# Run Optics tests

A GitHub Action that runs an [Optics](https://optics-framework.org) test suite (the `optics-framework` Python package) in CI.

It installs Optics and the engines you name, optionally validates the suite with `optics dry_run`, runs `optics execute`, writes the JUnit results to the job summary and uploads the run output (logs and screenshots) as an artifact.

## Usage

```yaml
name: Optics

on: [push, pull_request]

jobs:
  web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: mozarkai/optics-action@v1
        with:
          suite: tests/web          # folder with config.yaml, test_cases/, modules/
          extras: playwright
          optics-version: "1.11.0"  # pin it; upgrade on purpose
          dry-run: true
```

The suite in [`examples/web`](examples/web) is a working example: it opens example.com in headless Chromium and checks one line of text. It is the sample from `optics init --template playwright` with `headless: true` set in `config.yaml`.

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `suite` | yes | | Path to the Optics project folder. |
| `extras` | no | `playwright` | Comma-separated `optics-framework` extras: `playwright`, `selenium`, `appium`, `web`, `mobile`, `easyocr`, `vision`, `llm`, `all`. With `playwright`, `web` or `all`, the action also runs `playwright install --with-deps chromium`. |
| `optics-version` | no | `latest` | Version of `optics-framework` to install, such as `1.11.0`. |
| `python-version` | no | `3.12` | Python version. Optics needs 3.12 or newer. |
| `args` | no | | Extra arguments appended to `optics execute`. |
| `dry-run` | no | `false` | Run `optics dry_run` on the suite before executing it. |

## Outputs

| Output | Description |
|---|---|
| `junit` | Path to the JUnit XML report, `<suite>/execution_output/junit_output.xml`. |

## Pass or fail

The job fails when `optics execute` exits non-zero, which it does when any test case fails. The summary step also fails the job when the JUnit report lists a failure. That catches [error screens](https://optics-framework.org/docs/run/error-detection) found at the end of a run, which Optics adds to the report without changing its exit code.

On Linux the suite runs under `xvfb-run`, so a suite with `headless: false` still works on a runner with no display.

The run output folder is uploaded as one archive, `optics-output.tgz`, because screenshot file names can contain colons, which `upload-artifact` rejects. The artifact is named `optics-output-<job>-<matrix index>`.

## Android emulator

Android suites need an emulator and an Appium server on the runner. The [Run tests in CI](https://optics-framework.org/docs/run/ci) page has the full recipe. The emulator runner action runs everything in its own `script`, so to use this action, boot the emulator in a step of its own and leave it running:

```yaml
jobs:
  android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - name: Enable KVM
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules
          sudo udevadm trigger --name-match=kvm

      - name: Start an emulator
        run: |
          image="system-images;android-34;google_apis;x86_64"
          yes | "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "$image" "emulator"
          echo no | "$ANDROID_HOME/cmdline-tools/latest/bin/avdmanager" create avd -n ci -k "$image"
          "$ANDROID_HOME/emulator/emulator" -avd ci -no-window -no-audio -no-boot-anim -no-snapshot &
          adb wait-for-device
          until [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" = 1 ]; do sleep 2; done
          adb install app/build/outputs/apk/debug/app-debug.apk

      - uses: actions/setup-node@v7
        with:
          node-version: 22

      - name: Start Appium
        run: |
          npm install -g appium
          appium driver install uiautomator2
          appium > appium.log 2>&1 &
          sleep 5

      - uses: mozarkai/optics-action@v1
        with:
          suite: tests/android
          extras: appium
          optics-version: "1.11.0"
```

Set `deviceName` in `config.yaml` to `emulator-5554` (the first emulator) and make `appPackage` and `appActivity` match the app you install.

## Tips

These follow the [CI guide](https://optics-framework.org/docs/run/ci):

- Pin `optics-version` so a new release doesn't change behavior mid-sprint.
- Use `dry-run: true` to catch typos in seconds, before paying for a browser or emulator.
- Pass API keys such as `GEMINI_API_KEY` as secrets in `env`, never in the suite.
- Put `Assert Presence` before steps that follow a screen change. Runners are slower than laptops.

## License

[Apache-2.0](LICENSE)
