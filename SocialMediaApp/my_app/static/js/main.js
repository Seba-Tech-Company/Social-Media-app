document.addEventListener("DOMContentLoaded", () => {
    const themeButton = document.getElementById("themeButton");
    let darkMode = false;

    themeButton.addEventListener("click", () => {
        if (!darkMode) {
            document.body.style.background = "#1e1e1e";
            themeButton.textContent = "☀️ Light Mode";
        } else {
            document.body.style.background = "url('../images/background.jpg') no-repeat center center/cover";
            themeButton.textContent = "🌙 Dark Mode";
        }
        darkMode = !darkMode;
    });
});
