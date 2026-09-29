// Comic Craft Giri - Studio Frontend Controller

document.addEventListener("DOMContentLoaded", () => {
  const root = document.documentElement;
  const themeToggle = document.querySelector(".theme-toggle");
  const themeLabel = document.querySelector(".theme-toggle-label");

  // 1. Theme Management (Day / Night Mode)
  const savedTheme = localStorage.getItem("comic-craft-theme");
  if (savedTheme === "light" || savedTheme === "dark") {
    root.dataset.theme = savedTheme;
  }

  function syncThemeButton() {
    if (!themeToggle || !themeLabel) return;
    const isDark = root.dataset.theme === "dark" || 
      (!root.dataset.theme && window.matchMedia("(prefers-color-scheme: dark)").matches);
    themeLabel.textContent = isDark ? "Day mode" : "Night mode";
    themeToggle.setAttribute("aria-pressed", String(isDark));
  }

  syncThemeButton();

  if (themeToggle) {
    themeToggle.addEventListener("click", () => {
      const isDark = root.dataset.theme === "dark";
      root.dataset.theme = isDark ? "light" : "dark";
      localStorage.setItem("comic-craft-theme", root.dataset.theme);
      syncThemeButton();
    });
  }

  // 2. Settings Dropdown & Custom Setting Toggle
  const settingSelect = document.getElementById("setting_select");
  const customSettingContainer = document.getElementById("custom_setting_container");
  const settingFinalInput = document.getElementById("setting");
  const customSettingInput = document.getElementById("custom_setting_input");

  function updateSettingValue() {
    if (!settingSelect || !settingFinalInput) return;
    if (settingSelect.value === "CUSTOM") {
      if (customSettingContainer) customSettingContainer.style.display = "block";
      settingFinalInput.value = (customSettingInput && customSettingInput.value.trim()) || "Enchanted Realm";
    } else {
      if (customSettingContainer) customSettingContainer.style.display = "none";
      settingFinalInput.value = settingSelect.value;
    }
  }

  if (settingSelect) {
    settingSelect.addEventListener("change", updateSettingValue);
  }
  if (customSettingInput) {
    customSettingInput.addEventListener("input", updateSettingValue);
  }

  // 3. Inspiration Chips Handler
  const chips = document.querySelectorAll(".prompt-chip");
  const promptInput = document.getElementById("story_prompt");
  const characterInput = document.getElementById("character_name");
  const toneSelect = document.getElementById("story_tone");
  const styleSelect = document.getElementById("art_style");

  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const prompt = chip.getAttribute("data-prompt") || "";
      const hero = chip.getAttribute("data-hero") || "";
      const setting = chip.getAttribute("data-setting") || "";
      const tone = chip.getAttribute("data-tone") || "";
      const style = chip.getAttribute("data-style") || "";

      if (promptInput && prompt) promptInput.value = prompt;
      if (characterInput && hero) characterInput.value = hero;
      if (toneSelect && tone) toneSelect.value = tone;
      if (styleSelect && style) styleSelect.value = style;

      if (settingSelect) {
        let found = false;
        for (let opt of settingSelect.options) {
          if (opt.value.toLowerCase().includes(setting.toLowerCase()) || setting.toLowerCase().includes(opt.value.toLowerCase())) {
            settingSelect.value = opt.value;
            found = true;
            break;
          }
        }
        if (!found) {
          settingSelect.value = "CUSTOM";
          if (customSettingInput) customSettingInput.value = setting;
        }
        updateSettingValue();
      }

      chip.style.transform = "scale(0.95)";
      setTimeout(() => { chip.style.transform = "scale(1)"; }, 150);
    });
  });

  // 4. Form Submission and Progress Overlay
  const form = document.getElementById("comic-form");
  const progressOverlay = document.getElementById("progress-overlay");
  const stepItems = document.querySelectorAll(".stepper-item");

  if (form && progressOverlay) {
    form.addEventListener("submit", (e) => {
      updateSettingValue();
      if (!promptInput.value.trim() || !characterInput.value.trim() || !settingFinalInput.value.trim()) {
        return;
      }

      progressOverlay.classList.add("active");

      const steps = [
        { index: 0, delay: 500 },
        { index: 1, delay: 2500 },
        { index: 2, delay: 5000 },
        { index: 3, delay: 8500 }
      ];

      steps.forEach(({ index, delay }) => {
        setTimeout(() => {
          stepItems.forEach((item, i) => {
            if (i < index) {
              item.classList.remove("active");
              item.classList.add("done");
              const icon = item.querySelector(".stepper-icon");
              if (icon) icon.textContent = "[OK]";
            } else if (i === index) {
              item.classList.add("active");
            }
          });
        }, delay);
      });
    });
  }
});
