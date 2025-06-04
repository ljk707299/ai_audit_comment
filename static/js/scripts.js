// scripts.js

document.addEventListener('DOMContentLoaded', function () {
    const passLinks = document.querySelectorAll('.comment a .pass');

    passLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            if (confirm('确认通过吗?')) {
                fetch(this.href, {
                    method: 'GET'
                }).then(
                    this.parentElement.remove()
                ).catch(error => {
                    console.error('Error:', error);
                });
            }
        });
    });


    const rejectLinks = document.querySelectorAll('.comment a .reject');

    rejectLinks.forEach(link => {
        link.addEventListener('click', function (event) {
            event.preventDefault();
            if (confirm('确认拒绝这条评论?')) {
                fetch(this.href, {
                    method: 'GET'
                }).then(
                    this.parentElement.remove()
                ).catch(error => {
                    console.error('Error:', error);
                });
            }
        });
    });

});
