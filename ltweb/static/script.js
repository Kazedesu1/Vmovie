let slideIndex = 0;
        const slides = document.querySelector('.slides');
        const totalSlides = document.querySelectorAll('.slide').length;

        function changeSlide(n) {
            slideIndex += n;
            if (slideIndex < 0) slideIndex = totalSlides - 1;
            if (slideIndex >= totalSlides) slideIndex = 0;
            updateSlidePosition();
        }

        function currentSlide(n) {
            slideIndex = n - 1;
            updateSlidePosition();
        }

        function updateSlidePosition() {
            slides.style.transform = 'translateX(' + (-slideIndex * 100) + '%)';
            updateDots();
        }

        function updateDots() {
            const dots = document.querySelectorAll('.dot');
            dots.forEach(dot => dot.classList.remove('active'));
            dots[slideIndex].classList.add('active');
        }

        // Auto-slide every 5 seconds
        setInterval(() => { changeSlide(1); }, 5000);



        function toggleForm(form) {
            const formWrapper = document.getElementById('formWrapper');
            if (form === 'signUp') {
                formWrapper.style.transform = 'translateX(0)';
            } else {
                formWrapper.style.transform = 'translateX(-50%)';
            }
        }

        // Check URL query parameter to show the correct form   
        const urlParams = new URLSearchParams(window.location.search);
        const form = urlParams.get('form');
        if (form === 'signup') {
            toggleForm('signUp');
        } else {
            toggleForm('login');
        }