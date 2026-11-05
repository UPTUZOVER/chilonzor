/* Chilonzor · APK tahlil — kichik interfeys yordamchilari (kutubxonasiz). */
(function () {
  "use strict";

  // CSRF tokenini cookie'dan formalarga yangilab qo'yish (orqaga qaytilganda eskirmasin).
  function getCookie(name) {
    var parts = (document.cookie || "").split("; ");
    for (var i = 0; i < parts.length; i += 1) {
      if (parts[i].indexOf(name + "=") === 0) {
        return decodeURIComponent(parts[i].slice(name.length + 1));
      }
    }
    return "";
  }

  function syncCsrfTokens() {
    var token = getCookie("csrftoken");
    if (!token) return;
    document.querySelectorAll("input[name='csrfmiddlewaretoken']").forEach(function (input) {
      input.value = token;
    });
  }

  document.addEventListener("submit", syncCsrfTokens, true);
  window.addEventListener("pageshow", syncCsrfTokens);
  syncCsrfTokens();

  // Tungi / kunduzgi rejim. Tanlov brauzerda saqlanadi; tanlanmagan bo'lsa
  // kompyuter sozlamasiga ergashadi.
  var themeToggle = document.querySelector("[data-theme-toggle]");
  var root = document.documentElement;
  var systemDark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;

  function currentTheme() {
    var chosen = root.getAttribute("data-theme");
    if (chosen === "dark" || chosen === "light") return chosen;
    return systemDark && systemDark.matches ? "dark" : "light";
  }

  function syncThemeButton() {
    if (!themeToggle) return;
    var dark = currentTheme() === "dark";
    var label = themeToggle.getAttribute(dark ? "data-label-light" : "data-label-dark");
    themeToggle.setAttribute("aria-label", label);
    themeToggle.setAttribute("title", label);
  }

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("theme", next);
      } catch (error) {}
      syncThemeButton();
    });
    if (systemDark && systemDark.addEventListener) {
      systemDark.addEventListener("change", syncThemeButton);
    }
    syncThemeButton();
  }

  // Mobil menyu.
  var toggle = document.querySelector("[data-nav-toggle]");
  if (toggle) {
    toggle.addEventListener("click", function () {
      var topbar = toggle.closest(".topbar");
      var open = topbar.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Tasdiq talab qiladigan formalar: <form data-confirm="...">.
  document.addEventListener("submit", function (event) {
    var form = event.target;
    var message = form.getAttribute && form.getAttribute("data-confirm");
    if (message && !window.confirm(message)) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  });

  // Butun qator bosiladigan jadvallar: <tr data-href="...">.
  document.addEventListener("click", function (event) {
    var row = event.target.closest("tr[data-href]");
    if (!row) return;
    if (event.target.closest("a, button, input, select, textarea, label, form")) return;
    if (window.getSelection && String(window.getSelection())) return;
    window.location.href = row.getAttribute("data-href");
  });

  // Nusxalash tugmasi: <button data-copy="qiymat">.
  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-copy]");
    if (!button) return;
    var value = button.getAttribute("data-copy");
    var done = function () {
      var original = button.getAttribute("aria-label");
      button.setAttribute("aria-label", button.getAttribute("data-copied") || "OK");
      button.classList.add("is-copied");
      window.setTimeout(function () {
        button.setAttribute("aria-label", original);
        button.classList.remove("is-copied");
      }, 1500);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(value).then(done);
    } else {
      var area = document.createElement("textarea");
      area.value = value;
      area.setAttribute("readonly", "");
      area.style.position = "absolute";
      area.style.left = "-9999px";
      document.body.appendChild(area);
      area.select();
      try {
        document.execCommand("copy");
        done();
      } finally {
        document.body.removeChild(area);
      }
    }
  });

  // Saqlanmagan tahlil izohi: yuborishdan oldin ogohlantirish.
  var noteForm = document.querySelector("[data-note-form]");
  if (noteForm) {
    var field = noteForm.querySelector("textarea");
    var flag = noteForm.querySelector("[data-note-dirty]");
    var initial = field ? field.value : "";
    var isDirty = function () {
      return field && field.value !== initial;
    };
    if (field && flag) {
      field.addEventListener("input", function () {
        flag.hidden = !isDirty();
      });
    }
    noteForm.addEventListener("submit", function () {
      initial = field ? field.value : "";
    });
    document.querySelectorAll("[data-guard-note]").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        if (isDirty() && !window.confirm(form.getAttribute("data-guard-note"))) {
          event.preventDefault();
          event.stopImmediatePropagation();
        }
      });
    });
  }
})();
