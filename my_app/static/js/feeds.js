document.addEventListener("DOMContentLoaded", function () {
    const likeButtons = document.querySelectorAll(".like-btn");

    likeButtons.forEach(button => {
        button.addEventListener("click", function () {
            const postId = this.getAttribute("data-id");

            fetch(`/like_post/${postId}`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById(`likes-${postId}`).textContent = data.new_likes;
                } else {
                    alert(data.message);
                }
            })
            .catch(error => console.error("Error:", error));
        });
    });
});
