document.addEventListener("DOMContentLoaded", function () {
    const searchContainer = document.querySelector(".search-container");
    const toggleButton = document.getElementById("toggle-search");
    const searchInput = document.getElementById("search-input");
    const clearButton = document.getElementById("clear-search");

    // Toggle search box
    toggleButton.addEventListener("click", function () {
        searchContainer.classList.toggle("active");
    });

    // Clear search input
    clearButton.addEventListener("click", function () {
        searchInput.value = "";
        searchInput.focus();
    });

    // Search event
    searchInput.addEventListener("input", function () {
        console.log("Searching for:", searchInput.value);
    });
});
