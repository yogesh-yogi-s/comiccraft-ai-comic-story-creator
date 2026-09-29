const root = document.documentElement;
const themeToggle = document.querySelector(".theme-toggle");
const themeLabel = document.querySelector(".theme-toggle-label");
const menuToggle = document.querySelector(".menu-toggle");
const primaryNav = document.querySelector(".primary-nav");

const savedTheme = localStorage.getItem("comic-craft-theme");
if (savedTheme === "light" || savedTheme === "dark") {
  root.dataset.theme = savedTheme;
} else {
  delete root.dataset.theme;
}

function syncThemeButton() {
  const explicitTheme = root.dataset.theme;
  const isDark = explicitTheme
    ? explicitTheme === "dark"
    : window.matchMedia("(prefers-color-scheme: dark)").matches;
  themeLabel.textContent = isDark ? "Day mode" : "Night mode";
  themeToggle.setAttribute("aria-pressed", String(isDark));
  document.querySelector('meta[name="theme-color"]').content = isDark ? "#1c211e" : "#f2f3ef";
}

syncThemeButton();
themeToggle.addEventListener("click", () => {
  const currentlyDark = themeToggle.getAttribute("aria-pressed") === "true";
  root.dataset.theme = currentlyDark ? "light" : "dark";
  localStorage.setItem("comic-craft-theme", root.dataset.theme);
  syncThemeButton();
});

menuToggle.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
  primaryNav.classList.toggle("is-open", !isOpen);
});

primaryNav.querySelectorAll("a").forEach((link) => {
  link.addEventListener("click", () => {
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open navigation");
    primaryNav.classList.remove("is-open");
  });
});

const revealItems = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12 });
  revealItems.forEach((item) => revealObserver.observe(item));
} else {
  revealItems.forEach((item) => item.classList.add("is-visible"));
}

const ideaForm = document.querySelector("#idea-form");
const ideaInput = document.querySelector("#idea");
const formatInput = document.querySelector("#format");
const briefOutput = document.querySelector("#brief-output");
const outputText = document.querySelector("#output-text");
const copyButton = document.querySelector("#copy-brief");
let generatedBrief = "";

ideaForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const idea = ideaInput.value.trim();
  if (!idea) {
    ideaInput.focus();
    return;
  }
  generatedBrief = `Comic Craft Giri - creative starting brief\nFormat: ${formatInput.value}\nIdea: ${idea}`;
  outputText.textContent = generatedBrief;
  briefOutput.hidden = false;
  copyButton.textContent = "Copy brief";
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(generatedBrief);
    copyButton.textContent = "Copied";
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(outputText);
    selection.removeAllRanges();
    selection.addRange(range);
    copyButton.textContent = "Select and copy";
  }
});
