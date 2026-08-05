/* ----------------- Start Document ----------------- */
(function ($) {
	"use strict";

	$(document).ready(function () {

		/*--------------------------------------------------*/
		/*  Mobile Menu - mmenu.js
		/*--------------------------------------------------*/
		$(function () {
			function mmenuInit() {
				var wi = $(window).width();
				if (wi <= '1099') {

					$(".mmenu-init").remove();
					$("#navigation").clone().addClass("mmenu-init").insertBefore("#navigation").removeAttr('id').removeClass('style-1 style-2')
						.find('ul, div').removeClass('style-1 style-2 mega-menu mega-menu-content mega-menu-section').removeAttr('id');
					$(".mmenu-init").find("ul").addClass("mm-listview");
					$(".mmenu-init").find(".mobile-styles .mm-listview").unwrap();


					$(".mmenu-init").mmenu({
						"counters": true
					}, {
						// configuration
						offCanvas: {
							pageNodetype: "#wrapper"
						}
					});

					var mmenuAPI = $(".mmenu-init").data("mmenu");
					var $icon = $(".mmenu-trigger .hamburger");

					$(".mmenu-trigger").on('click', function () {
						mmenuAPI.open();
					});

				}
				$(".mm-next").addClass("mm-fullsubopen");
			}
			mmenuInit();
			$(window).resize(function () { mmenuInit(); });
		});


		/*--------------------------------------------------*/
		/*  Sticky Header
		/*--------------------------------------------------*/
		function stickyHeader() {

			$(window).on('scroll load', function () {

				if ($(window).width() < '1099') {
					$("#header-container").removeClass("cloned");
				}

				if ($(window).width() > '1099') {

					// CSS adjustment
					$("#header-container").css({
						position: 'fixed',
					});

					var headerOffset = $("#header-container").height();

					if ($(window).scrollTop() >= headerOffset) {
						$("#header-container").addClass('cloned');
						$(".wrapper-with-transparent-header #header-container").addClass('cloned').removeClass("transparent-header unsticky");
					} else {
						$("#header-container").removeClass("cloned");
						$(".wrapper-with-transparent-header #header-container").addClass('transparent-header unsticky').removeClass("cloned");
					}

					// Sticky Logo
					var transparentLogo = $('#header-container #logo img').attr('data-transparent-logo');
					var stickyLogo = $('#header-container #logo img').attr('data-sticky-logo');

					if ($('.wrapper-with-transparent-header #header-container').hasClass('cloned')) {
						$("#header-container.cloned #logo img").attr("src", stickyLogo);
					}

					if ($('.wrapper-with-transparent-header #header-container').hasClass('transparent-header')) {
						$("#header-container #logo img").attr("src", transparentLogo);
					}

					$(window).on('load resize', function () {
						var headerOffset = $("#header-container").height();
						$("#wrapper").css({ 'padding-top': headerOffset });
					});
				}
			});
		}

		// Sticky Header Init
		stickyHeader();


		/*--------------------------------------------------*/
		/*  Transparent Header Spacer Adjustment
		/*--------------------------------------------------*/
		$(window).on('load resize', function () {
			var transparentHeaderHeight = $('.transparent-header').outerHeight();
			$('.transparent-header-spacer').css({
				height: transparentHeaderHeight,
			});
		});


		/*----------------------------------------------------*/
		/*  Back to Top
		/*----------------------------------------------------*/

		// Button
		function backToTop() {
			$('body').append('<div id="backtotop"><a href="#"></a></div>');
		}
		backToTop();

		// Showing Button
		var pxShow = 600; // height on which the button will show
		var scrollSpeed = 500; // how slow / fast you want the button to scroll to top.

		$(window).scroll(function () {
			if ($(window).scrollTop() >= pxShow) {
				$("#backtotop").addClass('visible');
			} else {
				$("#backtotop").removeClass('visible');
			}
		});

		$('#backtotop a').on('click', function () {
			$('html, body').animate({ scrollTop: 0 }, scrollSpeed);
			return false;
		});


		/*--------------------------------------------------*/
		/*  Ripple Effect
		/*--------------------------------------------------*/
		$('.ripple-effect, .ripple-effect-dark').on('click', function (e) {
			var rippleDiv = $('<span class="ripple-overlay">'),
				rippleOffset = $(this).offset(),
				rippleY = e.pageY - rippleOffset.top,
				rippleX = e.pageX - rippleOffset.left;

			rippleDiv.css({
				top: rippleY - (rippleDiv.height() / 2),
				left: rippleX - (rippleDiv.width() / 2),
				// background: $(this).data("ripple-color");
			}).appendTo($(this));

			window.setTimeout(function () {
				rippleDiv.remove();
			}, 800);
		});


		/*--------------------------------------------------*/
		/*  Interactive Effects
		/*--------------------------------------------------*/
		$(".switch, .radio").each(function () {
			var intElem = $(this);
			intElem.on('click', function () {
				intElem.addClass('interactive-effect');
				setTimeout(function () {
					intElem.removeClass('interactive-effect');
				}, 400);
			});
		});


		/*--------------------------------------------------*/
		/*  Sliding Button Icon
		/*--------------------------------------------------*/
		$(window).on('load', function () {
			$(".button.button-sliding-icon").not(".task-listing .button.button-sliding-icon").each(function () {
				var buttonWidth = $(this).outerWidth() + 30;
				$(this).css('width', buttonWidth);
			});
		});


		/*--------------------------------------------------*/
		/*  Sliding Button Icon
		/*--------------------------------------------------*/
		$('.bookmark-icon').on('click', function (e) {
			e.preventDefault();
			$(this).toggleClass('bookmarked');
		});

		$('.bookmark-button').on('click', function (e) {
			e.preventDefault();
			$(this).toggleClass('bookmarked');
		});


		/*----------------------------------------------------*/
		/*  Notifications Boxes
		/*----------------------------------------------------*/
		$("a.close").removeAttr("href").on('click', function () {
			function slideFade(elem) {
				var fadeOut = { opacity: 0, transition: 'opacity 0.5s' };
				elem.css(fadeOut).slideUp();
			}
			slideFade($(this).parent());
		});

		/*--------------------------------------------------*/
		/*  Notification Dropdowns
		/*--------------------------------------------------*/
		$(".header-notifications").each(function () {
			var userMenu = $(this);
			var userMenuTrigger = $(this).find('.header-notifications-trigger a');

			$(userMenuTrigger).on('click', function (event) {
				event.preventDefault();

				if ($(this).closest(".header-notifications").is(".active")) {
					close_user_dropdown();
				} else {
					close_user_dropdown();
					userMenu.addClass('active');
				}
			});
		});

		// Closing function
		function close_user_dropdown() {
			$('.header-notifications').removeClass("active");
		}

		// Closes notification dropdown on click outside the conatainer
		var mouse_is_inside = false;

		$(".header-notifications").on("mouseenter", function () {
			mouse_is_inside = true;
		});
		$(".header-notifications").on("mouseleave", function () {
			mouse_is_inside = false;
		});

		$("body").mouseup(function () {
			if (!mouse_is_inside) close_user_dropdown();
		});

		// Close with ESC
		$(document).keyup(function (e) {
			if (e.keyCode == 27) {
				close_user_dropdown();
			}
		});


		/*--------------------------------------------------*/
		/*  User Status Switch
		/*--------------------------------------------------*/
		if ($('.status-switch label.user-invisible').hasClass('current-status')) {
			$('.status-indicator').addClass('right');
		}

		$('.status-switch label.user-invisible').on('click', function () {
			$('.status-indicator').addClass('right');
			$('.status-switch label').removeClass('current-status');
			$('.user-invisible').addClass('current-status');
		});

		$('.status-switch label.user-online').on('click', function () {
			$('.status-indicator').removeClass('right');
			$('.status-switch label').removeClass('current-status');
			$('.user-online').addClass('current-status');
		});

		// $('.status-switch label.user-invisible').on('click', async function(){
		// 	updateUserStatus('inactive');
		// });

		// $('.status-switch label.user-online').on('click', async function(){
		// 	updateUserStatus('active');
		// });

		// async function updateUserStatus(newStatus) {
		// 	const statusIndicator = document.querySelector('.status-indicator');

		// 	// Update UI immediately
		// 	if (newStatus === 'inactive') {
		// 		statusIndicator.classList.add('right');
		// 		$('.status-switch label').removeClass('current-status');
		// 		$('.user-invisible').addClass('current-status');
		// 	} else {
		// 		statusIndicator.classList.remove('right');
		// 		$('.status-switch label').removeClass('current-status');
		// 		$('.user-online').addClass('current-status');
		// 	}

		// 	// Send request to backend
		// 	try {
		// 		const token = localStorage.getItem('access_token');
		// 		const response = await fetchProtected('/api/users/status/', {
		// 			method: 'PATCH',
		// 			body: JSON.stringify({ status: newStatus }),
		// 		});

		// 		if (response.ok) {
		// 			userInfo.status = newStatus;
		// 			console.log(`Status updated to ${newStatus}`);
		// 		} else {
		// 			console.error('Failed to update status');
		// 		}
		// 	} catch (error) {
		// 		console.error('Error updating status:', error);
		// 	}
		// }



		/*--------------------------------------------------*/
		/*  Full Screen Page Scripts
		/*--------------------------------------------------*/

		// Wrapper Height (window height - header height)
		function wrapperHeight() {
			var headerHeight = $("#header-container").outerHeight();
			var windowHeight = $(window).outerHeight() - headerHeight;
			$('.full-page-content-container, .dashboard-content-container, .dashboard-sidebar-inner, .dashboard-container, .full-page-container').css({ height: windowHeight });
			$('.dashboard-content-inner').css({ 'min-height': windowHeight });
		}

		// Enabling Scrollbar
		function fullPageScrollbar() {
			$(".full-page-sidebar-inner, .dashboard-sidebar-inner").each(function () {

				var headerHeight = $("#header-container").outerHeight();
				var windowHeight = $(window).outerHeight() - headerHeight;
				var sidebarContainerHeight = $(this).find(".sidebar-container, .dashboard-nav-container").outerHeight();

				// Enables scrollbar if sidebar is higher than wrapper
				if (sidebarContainerHeight > windowHeight) {
					$(this).css({ height: windowHeight });

				} else {
					$(this).find('.simplebar-track').hide();
				}
			});
		}

		// Init
		$(window).on('load resize', function () {
			wrapperHeight();
			fullPageScrollbar();
		});
		wrapperHeight();
		fullPageScrollbar();

		// Sliding Sidebar 
		$('.enable-filters-button').on('click', function () {
			$('.full-page-sidebar').toggleClass("enabled-sidebar");
			$(this).toggleClass("active");
			$('.filter-button-tooltip').removeClass('tooltip-visible');
		});

		/*  Enable Filters Button Tooltip */
		$(window).on('load', function () {
			$('.filter-button-tooltip').css({
				left: $('.enable-filters-button').outerWidth() + 48
			})
				.addClass('tooltip-visible');
		});

		// Avatar Switcher
		function avatarSwitcher() {
			var readURL = function (input) {
				if (input.files && input.files[0]) {
					var reader = new FileReader();

					reader.onload = function (e) {
						$('.profile-pic').attr('src', e.target.result);
					};

					reader.readAsDataURL(input.files[0]);
				}
			};

			$(".file-upload").on('change', function () {
				readURL(this);
			});

			$(".upload-button").on('click', function () {
				$(".file-upload").click();
			});
		} avatarSwitcher();


		/*----------------------------------------------------*/
		/* Dashboard Scripts
		/*----------------------------------------------------*/

		// Dashboard Nav Submenus
		$('.dashboard-nav ul li a').on('click', function (e) {
			if ($(this).closest("li").children("ul").length) {
				if ($(this).closest("li").is(".active-submenu")) {
					$('.dashboard-nav ul li').removeClass('active-submenu');
				} else {
					$('.dashboard-nav ul li').removeClass('active-submenu');
					$(this).parent('li').addClass('active-submenu');
				}
				e.preventDefault();
			}
		});


		// Responsive Dashbaord Nav Trigger
		$('.dashboard-responsive-nav-trigger').on('click', function (e) {
			e.preventDefault();
			$(this).toggleClass('active');

			var dashboardNavContainer = $('body').find(".dashboard-nav");

			if ($(this).hasClass('active')) {
				$(dashboardNavContainer).addClass('active');
			} else {
				$(dashboardNavContainer).removeClass('active');
			}

			$('.dashboard-responsive-nav-trigger .hamburger').toggleClass('is-active');

		});

		// Fun Facts
		function funFacts() {
			/*jslint bitwise: true */
			function hexToRgbA(hex) {
				var c;
				if (/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)) {
					c = hex.substring(1).split('');
					if (c.length == 3) {
						c = [c[0], c[0], c[1], c[1], c[2], c[2]];
					}
					c = '0x' + c.join('');
					return 'rgba(' + [(c >> 16) & 255, (c >> 8) & 255, c & 255].join(',') + ',0.07)';
				}
			}

			$(".fun-fact").each(function () {
				var factColor = $(this).attr('data-fun-fact-color');

				if (factColor !== undefined) {
					$(this).find(".fun-fact-icon").css('background-color', hexToRgbA(factColor));
					$(this).find("i").css('color', factColor);
				}
			});

		} funFacts();


		// Notes & Messages Scrollbar
		$(window).on('load resize', function () {
			var winwidth = $(window).width();
			if (winwidth > 1199) {

				// Notes
				$('.row').each(function () {
					var mbh = $(this).find('.main-box-in-row').outerHeight();
					var cbh = $(this).find('.child-box-in-row').outerHeight();
					if (mbh < cbh) {
						var headerBoxHeight = $(this).find('.child-box-in-row .headline').outerHeight();
						var mainBoxHeight = $(this).find('.main-box-in-row').outerHeight() - headerBoxHeight + 39;

						$(this).find('.child-box-in-row .content')
							.wrap('<div class="dashboard-box-scrollbar" style="max-height: ' + mainBoxHeight + 'px" data-simplebar></div>');
					}
				});

				// Messages Sidebar
				// var messagesList = $(".messages-inbox").outerHeight();
				// var messageWrap = $(".message-content").outerHeight();
				// if ( messagesList > messagesWrap) {
				// 	$(messagesList).css({
				// 		'max-height': messageWrap,
				// 	});
				// }
			}
		});

		// Mobile Adjustment for Single Button Icon in Dashboard Box
		$('.buttons-to-right').each(function () {
			var btr = $(this).width();
			if (btr < 36) {
				$(this).addClass('single-right-button');
			}
		});

		// Small Footer Adjustment
		$(window).on('load resize', function () {
			var smallFooterHeight = $('.small-footer').outerHeight();
			$('.dashboard-footer-spacer').css({
				'padding-top': smallFooterHeight + 45
			});
		});


		// Auto Resizing Message Input Field
		/* global jQuery */
		jQuery.each(jQuery('textarea[data-autoresize]'), function () {
			var offset = this.offsetHeight - this.clientHeight;

			var resizeTextarea = function (el) {
				jQuery(el).css('height', 'auto').css('height', el.scrollHeight + offset);
			};
			jQuery(this).on('keyup input', function () { resizeTextarea(this); }).removeAttr('data-autoresize');
		});


		/*--------------------------------------------------*/
		/*  Star Rating
		/*--------------------------------------------------*/
		function starRating(ratingElem) {

			$(ratingElem).each(function () {

				var dataRating = $(this).attr('data-rating');

				// Rating Stars Output
				function starsOutput(firstStar, secondStar, thirdStar, fourthStar, fifthStar) {
					return ('' +
						'<span class="' + firstStar + '"></span>' +
						'<span class="' + secondStar + '"></span>' +
						'<span class="' + thirdStar + '"></span>' +
						'<span class="' + fourthStar + '"></span>' +
						'<span class="' + fifthStar + '"></span>');
				}

				var fiveStars = starsOutput('star', 'star', 'star', 'star', 'star');

				var fourHalfStars = starsOutput('star', 'star', 'star', 'star', 'star half');
				var fourStars = starsOutput('star', 'star', 'star', 'star', 'star empty');

				var threeHalfStars = starsOutput('star', 'star', 'star', 'star half', 'star empty');
				var threeStars = starsOutput('star', 'star', 'star', 'star empty', 'star empty');

				var twoHalfStars = starsOutput('star', 'star', 'star half', 'star empty', 'star empty');
				var twoStars = starsOutput('star', 'star', 'star empty', 'star empty', 'star empty');

				var oneHalfStar = starsOutput('star', 'star half', 'star empty', 'star empty', 'star empty');
				var oneStar = starsOutput('star', 'star empty', 'star empty', 'star empty', 'star empty');

				// Rules
				if (dataRating >= 4.75) {
					$(this).append(fiveStars);
				} else if (dataRating >= 4.25) {
					$(this).append(fourHalfStars);
				} else if (dataRating >= 3.75) {
					$(this).append(fourStars);
				} else if (dataRating >= 3.25) {
					$(this).append(threeHalfStars);
				} else if (dataRating >= 2.75) {
					$(this).append(threeStars);
				} else if (dataRating >= 2.25) {
					$(this).append(twoHalfStars);
				} else if (dataRating >= 1.75) {
					$(this).append(twoStars);
				} else if (dataRating >= 1.25) {
					$(this).append(oneHalfStar);
				} else if (dataRating >= 0.75) {
					$(this).append(oneStar);
				} else {
					$(this).append(starsOutput('star empty', 'star empty', 'star empty', 'star empty', 'star empty'));
				}

			});

		} starRating('.star-rating');


		/*--------------------------------------------------*/
		/*  Enabling Scrollbar in User Menu
		/*--------------------------------------------------*/
		function userMenuScrollbar() {
			$(".header-notifications-scroll").each(function () {
				var scrollContainerList = $(this).find('ul');
				var itemsCount = scrollContainerList.children("li").length;
				var notificationItems;

				// Determines how many items are displayed based on items height
				/* jshint shadow:true */
				if (scrollContainerList.children("li").outerHeight() > 140) {
					var notificationItems = 2;
				} else {
					var notificationItems = 3;
				}


				// Enables scrollbar if more than 2 items
				if (itemsCount > notificationItems) {

					var listHeight = 0;

					$(scrollContainerList).find('li:lt(' + notificationItems + ')').each(function () {
						listHeight += $(this).height();
					});

					$(this).css({ height: listHeight });

				} else {
					$(this).css({ height: 'auto' });
					$(this).find('.simplebar-track').hide();
				}
			});
		}

		// Init
		userMenuScrollbar();


		/*--------------------------------------------------*/
		/*  Tippy JS 
		/*--------------------------------------------------*/
		/* global tippy */
		tippy('[data-tippy-placement]', {
			delay: 100,
			arrow: true,
			arrowType: 'sharp',
			size: 'regular',
			duration: 200,

			// 'shift-toward', 'fade', 'scale', 'perspective'
			animation: 'shift-away',

			animateFill: true,
			theme: 'dark',

			// How far the tooltip is from its reference element in pixels 
			distance: 10,

		});


		/*----------------------------------------------------*/
		/*	Accordion @Lewis Briffa
		/*----------------------------------------------------*/
		var accordion = (function () {

			var $accordion = $('.js-accordion');
			var $accordion_header = $accordion.find('.js-accordion-header');

			// default settings 
			var settings = {
				// animation speed
				speed: 400,

				// close all other accordion items if true
				oneOpen: false
			};

			return {
				// pass configurable object literal
				init: function ($settings) {
					$(document).on('click', '.js-accordion-header', function () {
						accordion.toggle($(this));
					});

					$.extend(settings, $settings);

					// ensure only one accordion is active if oneOpen is true
					if (settings.oneOpen && $('.js-accordion-item.active').length > 1) {
						$('.js-accordion-item.active:not(:first)').removeClass('active');
					}

					// reveal the active accordion bodies
					$('.js-accordion-item.active').find('> .js-accordion-body').show();
				},
				toggle: function ($this) {

					if (settings.oneOpen && $this[0] != $this.closest('.js-accordion').find('> .js-accordion-item.active > .js-accordion-header')[0]) {
						$this.closest('.js-accordion')
							.find('> .js-accordion-item')
							.removeClass('active')
							.find('.js-accordion-body')
							.slideUp();
					}

					// show/hide the clicked accordion item
					$this.closest('.js-accordion-item').toggleClass('active');
					$this.next().stop().slideToggle(settings.speed);
				}
			};
		})();

		$(document).ready(function () {
			accordion.init({ speed: 300, oneOpen: true });
		});


		/*--------------------------------------------------*/
		/*  Tabs
		/*--------------------------------------------------*/
		// $(window).on('load resize', function() {
		// if ($(".tabs")[0]){
		// 	$('.tabs').each(function() {

		// 		  var thisTab = $(this);

		// 		  // Intial Border Position
		// 		  var activePos = thisTab.find('.tabs-header .active').position();

		// 		  function changePos() {

		// 		    // Update Position
		// 		    activePos = thisTab.find('.tabs-header .active').position();

		// 		    // Change Position & Width
		// 		    thisTab.find('.tab-hover').stop().css({
		// 		      left: activePos.left,
		// 		      width: thisTab.find('.tabs-header .active').width()
		// 		    });
		// 		  }

		// 		  changePos();

		// 		  // Intial Tab Height
		// 		  var tabHeight = thisTab.find('.tab.active').outerHeight();

		// 		  // Animate Tab Height
		// 		  function animateTabHeight() {

		// 		    // Update Tab Height
		// 		    tabHeight = thisTab.find('.tab.active').outerHeight();

		// 		    // Animate Height
		// 		    thisTab.find('.tabs-content').stop().css({
		// 		      height: tabHeight + 'px'
		// 		    });
		// 		  }

		// 		  animateTabHeight();

		// 		  // Change Tab
		// 		  function changeTab() {
		// 		    var getTabId = thisTab.find('.tabs-header .active a').attr('data-tab-id');

		// 		    // Remove Active State
		// 		    thisTab.find('.tab').stop().fadeOut(300, function () {
		// 		      // Remove Class
		// 		      $(this).removeClass('active');
		// 		    }).hide();

		// 		    thisTab.find('.tab[data-tab-id="' + getTabId + '"]').stop().fadeIn(300, function () {
		// 		      // Add Class
		// 		      $(this).addClass('active');

		// 		      // Animate Height
		// 		      animateTabHeight();
		// 		    });
		// 		  }

		// 		  // Tabs
		// 		  thisTab.find('.tabs-header a').on('click', function (e) {
		// 		    e.preventDefault();

		// 		    // Tab Id
		// 		    var tabId = $(this).attr('data-tab-id');

		// 		    // Remove Active State
		// 		    thisTab.find('.tabs-header a').stop().parent().removeClass('active');

		// 		    // Add Active State
		// 		    $(this).stop().parent().addClass('active');

		// 		    changePos();

		// 		    // Update Current Itm
		// 		    tabCurrentItem = tabItems.filter('.active');

		// 		    // Remove Active State
		// 		    thisTab.find('.tab').stop().fadeOut(300, function () {
		// 		      // Remove Class
		// 		      $(this).removeClass('active');
		// 		    }).hide();

		// 		    // Add Active State
		// 		    thisTab.find('.tab[data-tab-id="' + tabId + '"]').stop().fadeIn(300, function () {
		// 		      // Add Class
		// 		      $(this).addClass('active');

		// 		      // Animate Height
		// 		      animateTabHeight();
		// 		    });
		// 		  });

		// 		  // Tab Items
		// 		  var tabItems = thisTab.find('.tabs-header ul li');

		// 		  // Tab Current Item
		// 		  var tabCurrentItem = tabItems.filter('.active');

		// 		  // Next Button
		// 		  thisTab.find('.tab-next').on('click', function (e) {
		// 		    e.preventDefault();

		// 		    var nextItem = tabCurrentItem.next();

		// 		    tabCurrentItem.removeClass('active');

		// 		    if (nextItem.length) {
		// 		      tabCurrentItem = nextItem.addClass('active');
		// 		    } else {
		// 		      tabCurrentItem = tabItems.first().addClass('active');
		// 		    }

		// 		    changePos();
		// 		    changeTab();
		// 		  });

		// 		  // Prev Button
		// 		  thisTab.find('.tab-prev').on('click', function (e) {
		// 		    e.preventDefault();

		// 		    var prevItem = tabCurrentItem.prev();

		// 		    tabCurrentItem.removeClass('active');

		// 		    if (prevItem.length) {
		// 		      tabCurrentItem = prevItem.addClass('active');
		// 		    } else {
		// 		      tabCurrentItem = tabItems.last().addClass('active');
		// 		    }

		// 		    changePos();
		// 		    changeTab();
		// 		  });
		//   	});
		// }
		// });


		$(document).ready(function () {

			$('.tabs').each(function () {

				const thisTab = $(this);
				const header = thisTab.find('.tabs-header');
				const tabs = thisTab.find('.tab');
				const items = header.find("ul li");

				let current = items.filter('.active');

				// Position hover bar
				function moveHover() {
					const pos = current.position();
					if (!pos) return;
					thisTab.find('.tab-hover').css({
						left: pos.left,
						width: current.outerWidth()
					});
				}

				// Adjust height smoothly
				function resizeHeight() {
					const activeTab = thisTab.find('.tab.active');
					thisTab.find('.tabs-content').css({
						height: activeTab.outerHeight()
					});
				}

				// Changing tab
				function showTab(tabId) {
					tabs.finish().removeClass('active').hide();
					const activeTab = tabs.filter(`[data-tab-id="${tabId}"]`);
					activeTab.fadeIn(200).addClass('active');

					resizeHeight();
					moveHover();
				}

				// Click handler for tabs
				header.find("a").off("click").on("click", function (e) {
					e.preventDefault();

					const tabId = $(this).data("tab-id");

					items.removeClass("active");
					current = $(this).parent().addClass("active");

					showTab(tabId);
				});

				// Next/Prev
				thisTab.find(".tab-next").off("click").on("click", function (e) {
					e.preventDefault();

					let next = current.next();
					if (!next.length) next = items.first();

					items.removeClass("active");
					current = next.addClass("active");

					showTab(current.find("a").data("tab-id"));
				});

				thisTab.find(".tab-prev").off("click").on("click", function (e) {
					e.preventDefault();

					let prev = current.prev();
					if (!prev.length) prev = items.last();

					items.removeClass("active");
					current = prev.addClass("active");

					showTab(current.find("a").data("tab-id"));
				});

				// Initial setup
				showTab(current.find("a").data("tab-id"));


				// Only run height/hover update on resize (no rebinding!)
				$(window).on("resize", function () {
					resizeHeight();
					moveHover();
				});
				setTimeout(() => {
					resizeHeight();
				}, 150);

			});

		});



		/*--------------------------------------------------*/
		/*  Keywords
		/*--------------------------------------------------*/
		$(".keywords-container").each(function () {

			var container = $(this);
			var keywordInput = $(this).find(".keyword-input");
			var keywordsList = $(this).find(".keywords-list");

			// adding keyword
			function addKeyword() {
				var rawValue = keywordInput.val();
				var value = rawValue.trim();

				// Optional max limit: only active when data-max-keywords is set on the container
				var maxKeywords = parseInt(container.attr("data-max-keywords"), 10);
				if (!isNaN(maxKeywords) && keywordsList.children(".keyword").length >= maxKeywords) {
					keywordInput.val("");
					return;
				}

				// Optional duplicate prevention: only active when data-unique-keywords="true"
				if (container.attr("data-unique-keywords") === "true") {
					var exists = false;
					keywordsList.find(".keyword-text").each(function () {
						if ($(this).text().trim().toLowerCase() === value.toLowerCase()) {
							exists = true;
						}
					});
					if (exists) {
						keywordInput.val("");
						return;
					}
				}

				// XSS-safe: set user text via .text() instead of concatenating into HTML
				var $newKeyword = $("<span class='keyword'><span class='keyword-remove'></span><span class='keyword-text'></span></span>");
				$newKeyword.find(".keyword-text").text(rawValue);
				keywordsList.append($newKeyword).trigger('resizeContainer');
				keywordInput.val("");
			}

			// add via enter key
			keywordInput.on('keyup', function (e) {
				if ((e.keyCode == 13) && (keywordInput.val() !== "")) {
					addKeyword();
				}
			});

			// add via button
			$('.keyword-input-button').on('click', function () {
				if ((keywordInput.val() !== "")) {
					addKeyword();
				}
			});

			// removing keyword
			$(document).on("click", ".keyword-remove", function () {
				$(this).parent().addClass('keyword-removed');

				function removeFromMarkup() {
					$(".keyword-removed").remove();
				}
				setTimeout(removeFromMarkup, 500);
				keywordsList.css({ 'height': 'auto' }).height();
			});


			// animating container height
			keywordsList.on('resizeContainer', function () {
				var heightnow = $(this).height();
				var heightfull = $(this).css({ 'max-height': 'auto', 'height': 'auto' }).height();

				$(this).css({ 'height': heightnow }).animate({ 'height': heightfull }, 200);
			});

			$(window).on('resize', function () {
				keywordsList.css({ 'height': 'auto' }).height();
			});

			// Auto Height for keywords that are pre-added
			$(window).on('load', function () {
				var keywordCount = $('.keywords-list').children("span").length;

				// Enables scrollbar if more than 3 items
				if (keywordCount > 0) {
					keywordsList.css({ 'height': 'auto' }).height();

				}
			});

		});

		// EXPORT THE REFRESH LOGIC
		window.refreshKeywordsUI = function () {
			$(".keywords-list").css({ 'height': 'auto' }).trigger('resizeContainer');
		};


		/*--------------------------------------------------*/
		/*  Bootstrap Range Slider
		/*--------------------------------------------------*/

		// Thousand Separator
		function ThousandSeparator(nStr) {
			nStr += '';
			var x = nStr.split('.');
			var x1 = x[0];
			var x2 = x.length > 1 ? '.' + x[1] : '';
			var rgx = /(\d+)(\d{3})/;
			while (rgx.test(x1)) {
				x1 = x1.replace(rgx, '$1' + ',' + '$2');
			}
			return x1 + x2;
		}

		// Bidding Slider Average Value
		var avgValue = (parseInt($('.bidding-slider').attr("data-slider-min")) + parseInt($('.bidding-slider').attr("data-slider-max"))) / 2;
		if ($('.bidding-slider').data("slider-value") === 'auto') {
			$('.bidding-slider').attr({ 'data-slider-value': avgValue });
		}

		// Bidding Slider Init
		$('.bidding-slider').slider();

		$(".bidding-slider").on("slide", function (slideEvt) {
			$("#biddingVal").text(ThousandSeparator(parseInt(slideEvt.value)));
		});
		$("#biddingVal").text(ThousandSeparator(parseInt($('.bidding-slider').val())));


		// Default Bootstrap Range Slider
		var currencyAttr = $(".range-slider").attr('data-slider-currency');

		$(".range-slider").slider({
			formatter: function (value) {
				return currencyAttr + ThousandSeparator(parseInt(value[0])) + " - " + currencyAttr + ThousandSeparator(parseInt(value[1]));
			}
		});

		$(".range-slider-single").slider();


		/*----------------------------------------------------*/
		/*  Payment Accordion
		/*----------------------------------------------------*/
		var radios = document.querySelectorAll('.payment-tab-trigger > input');

		for (var i = 0; i < radios.length; i++) {
			radios[i].addEventListener('change', expandAccordion);
		}

		function expandAccordion(event) {
			/* jshint validthis: true */
			var tabber = this.closest('.payment');
			var allTabs = tabber.querySelectorAll('.payment-tab');
			for (var i = 0; i < allTabs.length; i++) {
				allTabs[i].classList.remove('payment-tab-active');
			}
			event.target.parentNode.parentNode.classList.add('payment-tab-active');
		}

		$('.billing-cycle-radios').on("click", function () {
			if ($('.billed-yearly-radio input').is(':checked')) { $('.pricing-plans-container').addClass('billed-yearly'); }
			if ($('.billed-monthly-radio input').is(':checked')) { $('.pricing-plans-container').removeClass('billed-yearly'); }
		});


		/*--------------------------------------------------*/
		/*  Quantity Buttons
		/*--------------------------------------------------*/
		function qtySum() {
			var arr = document.getElementsByName('qtyInput');
			var tot = 0;
			for (var i = 0; i < arr.length; i++) {
				if (parseInt(arr[i].value))
					tot += parseInt(arr[i].value);
			}
		}
		qtySum();

		$(".qtyDec, .qtyInc").on("click", function () {

			var $button = $(this);
			var oldValue = $button.parent().find("input").val();

			if ($button.hasClass('qtyInc')) {
				$button.parent().find("input").val(parseFloat(oldValue) + 1);
			} else {
				if (oldValue > 1) {
					$button.parent().find("input").val(parseFloat(oldValue) - 1);
				} else {
					$button.parent().find("input").val(1);
				}
			}

			qtySum();
			$(".qtyTotal").addClass("rotate-x");

		});


		/*----------------------------------------------------*/
		/*  Inline CSS replacement for backgrounds
		/*----------------------------------------------------*/
		function inlineBG() {

			// Common Inline CSS
			$(".single-page-header, .intro-banner").each(function () {
				var attrImageBG = $(this).attr('data-background-image');

				if (attrImageBG !== undefined) {
					$(this).append('<div class="background-image-container"></div>');
					$('.background-image-container').css('background-image', 'url(' + attrImageBG + ')');
				}
			});

		} inlineBG();

		// Fix for intro banner with label
		$(".intro-search-field").each(function () {
			var bannerLabel = $(this).children("label").length;
			if (bannerLabel > 0) {
				$(this).addClass("with-label");
			}
		});

		// Photo Boxes
		$(".photo-box, .photo-section, .video-container").each(function () {
			var photoBox = $(this);
			var photoBoxBG = $(this).attr('data-background-image');

			if (photoBox !== undefined) {
				$(this).css('background-image', 'url(' + photoBoxBG + ')');
			}
		});


		/*----------------------------------------------------*/
		/*  Share URL and Buttons
		/*----------------------------------------------------*/
		/* global ClipboardJS */
		$('.copy-url input').val(window.location.href);
		new ClipboardJS('.copy-url-button');

		$(".share-buttons-icons a").each(function () {
			var buttonBG = $(this).attr("data-button-color");
			if (buttonBG !== undefined) {
				$(this).css('background-color', buttonBG);
			}
		});


		/*----------------------------------------------------*/
		/*  Tabs
		/*----------------------------------------------------*/
		var $tabsNav = $('.popup-tabs-nav'),
			$tabsNavLis = $tabsNav.children('li');

		$tabsNav.each(function () {
			var $this = $(this);

			$this.next().children('.popup-tab-content').stop(true, true).hide().first().show();
			$this.children('li').first().addClass('active').stop(true, true).show();
		});

		$tabsNavLis.on('click', function (e) {
			var $this = $(this);

			$this.siblings().removeClass('active').end().addClass('active');

			$this.parent().next().children('.popup-tab-content').stop(true, true).hide()
				.siblings($this.find('a').attr('href')).fadeIn();

			e.preventDefault();
		});

		var hash = window.location.hash;
		var anchor = $('.tabs-nav a[href="' + hash + '"]');
		if (anchor.length === 0) {
			$(".popup-tabs-nav li:first").addClass("active").show(); //Activate first tab
			$(".popup-tab-content:first").show(); //Show first tab content
		} else {
			anchor.parent('li').click();
		}

		// Link to Register Tab
		$('.register-tab').on('click', function (event) {
			event.preventDefault();
			$(".popup-tab-content").hide();
			$("#register.popup-tab-content").show();
			$("body").find('.popup-tabs-nav a[href="#register"]').parent("li").click();
		});

		// Disable tabs if there's only one tab
		$('.popup-tabs-nav').each(function () {
			var listCount = $(this).find("li").length;
			if (listCount < 2) {
				$(this).css({
					'pointer-events': 'none'
				});
			}
		});


		/*----------------------------------------------------*/
		/*  Indicator Bar
		/*----------------------------------------------------*/
		$('.indicator-bar').each(function () {
			var indicatorLenght = $(this).attr('data-indicator-percentage');
			$(this).find("span").css({
				width: indicatorLenght + "%"
			});
		});


		/*----------------------------------------------------*/
		/*  Custom Upload Button
		/*----------------------------------------------------*/

		var uploadButton = {
			$button: $('.uploadButton-input'),
			$nameField: $('.uploadButton-file-name')
		};

		uploadButton.$button.on('change', function () {
			_populateFileField($(this));
		});

		function _populateFileField($button) {
			var selectedFile = [];
			for (var i = 0; i < $button.get(0).files.length; ++i) {
				selectedFile.push($button.get(0).files[i].name + '<br>');
			}
			uploadButton.$nameField.html(selectedFile);
		}


		/*----------------------------------------------------*/
		/*  Slick Carousel
		/*----------------------------------------------------*/
		$('.default-slick-carousel').slick({
			infinite: false,
			slidesToShow: 3,
			slidesToScroll: 1,
			dots: false,
			arrows: true,
			adaptiveHeight: true,
			responsive: [
				{
					breakpoint: 1292,
					settings: {
						dots: true,
						arrows: false
					}
				},
				{
					breakpoint: 993,
					settings: {
						slidesToShow: 2,
						slidesToScroll: 2,
						dots: true,
						arrows: false
					}
				},
				{
					breakpoint: 769,
					settings: {
						slidesToShow: 1,
						slidesToScroll: 1,
						dots: true,
						arrows: false
					}
				}
			]
		});


		$('.testimonial-carousel').slick({
			centerMode: true,
			centerPadding: '30%',
			slidesToShow: 1,
			dots: false,
			arrows: true,
			adaptiveHeight: true,
			responsive: [
				{
					breakpoint: 1600,
					settings: {
						centerPadding: '21%',
						slidesToShow: 1,
					}
				},
				{
					breakpoint: 993,
					settings: {
						centerPadding: '15%',
						slidesToShow: 1,
					}
				},
				{
					breakpoint: 769,
					settings: {
						centerPadding: '5%',
						dots: true,
						arrows: false
					}
				}
			]
		});


		$('.logo-carousel').slick({
			infinite: true,
			slidesToShow: 5,
			slidesToScroll: 1,
			dots: false,
			arrows: true,
			responsive: [
				{
					breakpoint: 1365,
					settings: {
						slidesToShow: 5,
						dots: true,
						arrows: false
					}
				},
				{
					breakpoint: 992,
					settings: {
						slidesToShow: 3,
						dots: true,
						arrows: false
					}
				},
				{
					breakpoint: 768,
					settings: {
						slidesToShow: 1,
						dots: true,
						arrows: false
					}
				}
			]
		});

		$('.blog-carousel').slick({
			infinite: false,
			slidesToShow: 3,
			slidesToScroll: 1,
			dots: false,
			arrows: true,
			responsive: [
				{
					breakpoint: 1365,
					settings: {
						slidesToShow: 3,
						dots: true,
						arrows: false
					}
				},
				{
					breakpoint: 992,
					settings: {
						slidesToShow: 2,
						dots: true,
						arrows: false
					}
				},
				{
					breakpoint: 768,
					settings: {
						slidesToShow: 1,
						dots: true,
						arrows: false
					}
				}
			]
		});

		/*----------------------------------------------------*/
		/*  Magnific Popup
		/*----------------------------------------------------*/
		$('.mfp-gallery-container').each(function () { // the containers for all your galleries

			$(this).magnificPopup({
				type: 'image',
				delegate: 'a.mfp-gallery',

				fixedContentPos: true,
				fixedBgPos: true,

				overflowY: 'auto',

				closeBtnInside: false,
				preloader: true,

				removalDelay: 0,
				mainClass: 'mfp-fade',

				gallery: { enabled: true, tCounter: '' }
			});
		});

		$(document).magnificPopup({
			delegate: '.popup-with-zoom-anim',
			type: 'inline',
			fixedContentPos: false,
			fixedBgPos: true,
			overflowY: 'auto',
			closeBtnInside: true,
			preloader: false,
			midClick: true,
			removalDelay: 300,
			mainClass: 'my-mfp-zoom-in'
		});

		$('.popup-with-zoom-anim').magnificPopup({
			type: 'inline',

			fixedContentPos: false,
			fixedBgPos: true,

			overflowY: 'auto',

			closeBtnInside: true,
			preloader: false,

			midClick: true,
			removalDelay: 300,
			mainClass: 'my-mfp-zoom-in'
		});

		$('.mfp-image').magnificPopup({
			type: 'image',
			closeOnContentClick: true,
			mainClass: 'mfp-fade',
			image: {
				verticalFit: true
			}
		});

		$('.popup-youtube, .popup-vimeo, .popup-gmaps').magnificPopup({
			disableOn: 700,
			type: 'iframe',
			mainClass: 'mfp-fade',
			removalDelay: 160,
			preloader: false,

			fixedContentPos: false
		});



		// ------------------ End Document ------------------ //

	});

})(this.jQuery);

function capitalize(str) {
	// Split the input string into an array of words
	str = str.split(" ");

	// Iterate through each word in the array
	for (var i = 0, x = str.length; i < x; i++) {
		// Capitalize the first letter of each word and concatenate it with the rest of the word
		str[i] = str[i][0].toUpperCase() + str[i].substr(1);
	}

	// Join the modified array of words back into a string
	return str.join(" ");
}


// Helper: Time since
function timeSince(dateString) {
	const pastDate = new Date(dateString);
	const now = new Date();

	// Get the difference in milliseconds
	const diffMs = now - pastDate;

	if (isNaN(diffMs) || diffMs < 0) {
		return "Invalid or future date";
	}

	// Convert to minutes, hours, days
	const diffMinutes = Math.floor(diffMs / (1000 * 60));
	const diffHours = Math.floor(diffMinutes / 60);
	const diffDays = Math.floor(diffHours / 24);

	const days = diffDays;
	const hours = diffHours % 24;
	const minutes = diffMinutes % 60;

	// Build readable format
	let result = "";
	if (days > 0) result += `${days} day${days > 1 ? "s" : ""} `;
	if (hours > 0) result += `${hours} hr${hours > 1 ? "s" : ""} `;
	if (minutes > 0) result += `${minutes} min${minutes > 1 ? "s" : ""}`;

	return result.trim() || "Just now";
}


// ========== CREATE BOOKMARK - added here so it will be on all pages ==========
async function createBookmark(model_type, object_id) {
	try {
		const res = await fetchProtected('/api/bookmarks/create/', {
			method: "POST",
			body: JSON.stringify({ model_type, object_id }),
		});
		if (!res || !res.ok) return null;
		const data = await res.json();
		console.log("Bookmark Created:", data);
		return data;
	} catch (err) {
		console.error("Error Creating Bookmark:", err);
		return null;
	}
}

// ========== DELETE BOOKMARK ==========
async function deleteBookmark(bookmark_id) {
	try {
		const res = await fetchProtected(`/api/bookmarks/${bookmark_id}/delete/`, {
			method: "DELETE",
		});
		if (res && (res.status === 204 || res.ok)) {
			console.log(`Bookmark ${bookmark_id} deleted successfully`);
			return true;
		}
		return false;
	} catch (err) {
		console.error("Error Deleting Bookmark:", err);
		return false;
	}
}

async function bookmarkHandling(operation, model_type, bookmarkbutton = null) {
	if (operation === "create") {
		const profileId = bookmarkbutton.getAttribute(`data-${model_type}-id`);
		const data = await createBookmark(model_type, profileId);
		if (data && data.id) {
			bookmarkbutton.setAttribute("data-bookmark-id", data.id);
			return true;
		}
		return false;
	}
	const bookmarkId = bookmarkbutton.getAttribute("data-bookmark-id");
	if (!bookmarkId) return false;
	const ok = await deleteBookmark(bookmarkId);
	if (ok) bookmarkbutton.removeAttribute("data-bookmark-id");
	return ok;
}

// Returns { profileId: bookmarkId } for the current user's bookmarked freelancers.
// Empty object for guests (no error, no request).
async function getBookmarkedProfileMap() {
	try {
		if (!(await isAuthenticated())) return {};
		const res = await fetchProtected('/api/bookmarks/');
		if (!res || !res.ok) return {};
		const data = await res.json();
		const map = {};
		(data.userprofiles || []).forEach(b => { map[b.profile_id] = b.id; });
		return map;
	} catch (err) {
		console.error("Error loading bookmarks:", err);
		return {};
	}
}

// Returns { objectId: bookmarkId } for the current user's bookmarks of the given
// model_type ("job" | "task" | "userprofile"). Empty object for guests.
async function getBookmarkMap(model_type) {
	try {
		if (!(await isAuthenticated())) return {};
		const res = await fetchProtected('/api/bookmarks/');
		if (!res || !res.ok) return {};
		const data = await res.json();
		const config = {
			job: { list: data.jobs, key: "job_id" },
			task: { list: data.tasks, key: "task_id" },
			userprofile: { list: data.userprofiles, key: "profile_id" },
		};
		const cfg = config[model_type];
		if (!cfg) return {};
		const map = {};
		(cfg.list || []).forEach(b => { map[b[cfg.key]] = b.id; });
		return map;
	} catch (err) {
		console.error("Error loading bookmarks:", err);
		return {};
	}
}

// Wires a single-page ".bookmark-button": seeds its initial bookmarked state and
// toggles create/delete on click. Used by the job/task/freelancer detail pages.
async function initBookmarkButton(bookmarkButton, model_type, objectId) {
	if (!bookmarkButton || !objectId) return;
	bookmarkButton.setAttribute(`data-${model_type}-id`, objectId);

	bookmarkButton.addEventListener("click", async () => {
		if (!await requireLogin()) return;
		const isBookmarked = bookmarkButton.classList.contains("bookmarked");
		bookmarkButton.style.pointerEvents = "none";
		const ok = await bookmarkHandling(isBookmarked ? "delete" : "create", model_type, bookmarkButton);
		bookmarkButton.style.pointerEvents = "";
		if (ok) bookmarkButton.classList.toggle("bookmarked", !isBookmarked);
	});

	// Seed initial state (only returns data for logged-in users).
	const map = await getBookmarkMap(model_type);
	if (map[objectId] != null) {
		bookmarkButton.classList.add("bookmarked");
		bookmarkButton.setAttribute("data-bookmark-id", map[objectId]);
	}
}

function starRating(ratingElem) {

	$(ratingElem).each(function () {

		var dataRating = $(this).attr('data-rating');

		// Rating Stars Output
		function starsOutput(firstStar, secondStar, thirdStar, fourthStar, fifthStar) {
			return ('' +
				'<span class="' + firstStar + '"></span>' +
				'<span class="' + secondStar + '"></span>' +
				'<span class="' + thirdStar + '"></span>' +
				'<span class="' + fourthStar + '"></span>' +
				'<span class="' + fifthStar + '"></span>');
		}

		var fiveStars = starsOutput('star', 'star', 'star', 'star', 'star');

		var fourHalfStars = starsOutput('star', 'star', 'star', 'star', 'star half');
		var fourStars = starsOutput('star', 'star', 'star', 'star', 'star empty');

		var threeHalfStars = starsOutput('star', 'star', 'star', 'star half', 'star empty');
		var threeStars = starsOutput('star', 'star', 'star', 'star empty', 'star empty');

		var twoHalfStars = starsOutput('star', 'star', 'star half', 'star empty', 'star empty');
		var twoStars = starsOutput('star', 'star', 'star empty', 'star empty', 'star empty');

		var oneHalfStar = starsOutput('star', 'star half', 'star empty', 'star empty', 'star empty');
		var oneStar = starsOutput('star', 'star empty', 'star empty', 'star empty', 'star empty');

		// Rules
		if (dataRating >= 4.75) {
			$(this).append(fiveStars);
		} else if (dataRating >= 4.25) {
			$(this).append(fourHalfStars);
		} else if (dataRating >= 3.75) {
			$(this).append(fourStars);
		} else if (dataRating >= 3.25) {
			$(this).append(threeHalfStars);
		} else if (dataRating >= 2.75) {
			$(this).append(threeStars);
		} else if (dataRating >= 2.25) {
			$(this).append(twoHalfStars);
		} else if (dataRating >= 1.75) {
			$(this).append(twoStars);
		} else if (dataRating >= 1.25) {
			$(this).append(oneHalfStar);
		} else if (dataRating >= 0.75) {
			$(this).append(oneStar);
		} else {
			$(this).append(starsOutput('star empty', 'star empty', 'star empty', 'star empty', 'star empty'));
		}

	});

}

// Get reviews received by a user
async function getReviewsReceived(userId) {
	try {
		const res = await fetch(`/api/reviews/user/${userId}/`, {
		});
		const data = await res.json();
		console.log("Reviews Received:", data);
		return data;
	} catch (err) {
		console.error("Error fetching reviews received:", err);
	}
}

// Show element based on user role
function showForRole(role, elementId, displayType = 'block') {
	document.addEventListener("data-ready", () => {
		if (!userInfo || !userInfo.role) return; // if user not logged in
		const el = document.getElementById(elementId);
		if (!el) return; // element not found
		if (userInfo.role === role) {
			el.style.display = displayType;
		} else {
			el.style.display = 'none';
		}
	});
}

// Freelancer-only sidebar links (present on every dashboard page via the shared
// sidebar partial). No-ops where the element isn't on the page.
showForRole("freelancer", "verify-identity-element");
showForRole("freelancer", "my-applications-element");
// Payments is employer-only; freelancers use the Wallet instead. Both roles keep
// the Billing & Subscription link.
showForRole("employer", "payments-nav-element");
showForRole("freelancer", "wallet-nav-element");
// "My Active Bids" (freelancer) and the employer "Jobs"/"Tasks" dropdowns are part
// of the shared sidebar too, so toggle them globally rather than relying on each
// page's inline script (which some pages, e.g. My Profile/Offers/Contracts/Billing,
// don't include).
showForRole("freelancer", "my-active-bid-element");
showForRole("employer", "jobs-id");
showForRole("employer", "tasks-id");


// update user status
async function updateUserNavInfo() {

	const rightSideNav = document.getElementById("right-side-nav");
	const userMenu = rightSideNav.querySelector(".header-widget"); // user profile section

	// Check authentication
	const authenticated = await isAuthenticated();

	if (!authenticated || !userInfo) {
		// if current page is not login page
		if (window.location.pathname !== "/login/") {
			rightSideNav.innerHTML = `
		<div class="header-widget">
			<a href="/login/" class="log-in-button"><i class="icon-feather-log-in"></i> <span>Log In / Register</span></a>
		</div>

		<!-- Mobile Navigation Button -->
		<span class="mmenu-trigger">
			<button class="hamburger hamburger--collapse" type="button">
				<span class="hamburger-box">
					<span class="hamburger-inner"></span>
				</span>
			</button>
		</span>`;
		} else {
			rightSideNav.innerHTML = `
		<div class="header-widget">
			<a href="/register/" class="log-in-button"><i class="icon-feather-log-in"></i> <span>Register</span></a>
		</div>

		<!-- Mobile Navigation Button -->
		<span class="mmenu-trigger">
			<button class="hamburger hamburger--collapse" type="button">
				<span class="hamburger-box">
					<span class="hamburger-inner"></span>
				</span>
			</button>
		</span>`;
		}

		rightSideNav.style.display = "block";

		// rightSideNav.innerHTML = `
		// 	<div class="header-widget">
		// 		<a href="/login/" class="popup-with-zoom-anim log-in-button"><i class="icon-feather-log-in"></i> <span>Log In / Register</span></a>
		// 	</div>

		// 	<!-- Mobile Navigation Button -->
		// 	<span class="mmenu-trigger">
		// 		<button class="hamburger hamburger--collapse" type="button">
		// 			<span class="hamburger-box">
		// 				<span class="hamburger-inner"></span>
		// 			</span>
		// 		</button>
		// 	</span>`;
		return;
	}

	// ---- User is authenticated ----
	// Update avatar images
	const avatarImages = rightSideNav.querySelectorAll(".user-avatar img");
	avatarImages.forEach(img => {
		img.src = userInfo.avatar_url || "/static/images/user-avatar-placeholder.png";
		img.alt = userInfo.full_name || "User";
		img.onerror = function () { this.src = "/static/images/user-avatar-placeholder.png"; };
	});

	// Update user name and role
	const nameEl = rightSideNav.querySelector(".user-name");
	const roleEl = document.createElement("span");

	if (nameEl) nameEl.innerHTML = `${userInfo.full_name != "" ? (capitalize(userInfo.full_name)) : userInfo.email} `;
	if (roleEl) roleEl.textContent = capitalize(userInfo.role) || "";

	// Append role next to name
	if (nameEl && roleEl && !nameEl.contains(roleEl)) {
		nameEl.appendChild(roleEl);
	}

	// Update online/invisible status indicator
	const statusContainer = document.getElementById("snackbar-user-status");
	const onlineEl = statusContainer?.querySelector(".user-online");
	const invisibleEl = statusContainer?.querySelector(".user-invisible");
	const indicatorEl = statusContainer?.querySelector(".status-indicator");

	if (statusContainer) {
		if (userInfo.status === "active") {
			onlineEl.classList.add("current-status");
			invisibleEl.classList.remove("current-status");
			indicatorEl.classList.remove("right");
			document.querySelectorAll(".user-avatar").forEach(el => {
				el.classList.remove("status-invisible");
				el.classList.add("status-online");
			});
		} else {
			onlineEl.classList.remove("current-status");
			invisibleEl.classList.add("current-status");
			indicatorEl.classList.add("right");
			document.querySelectorAll(".user-avatar").forEach(el => {
				el.classList.remove("status-online");
				el.classList.add("status-invisible");
			});
		}
	}

	// Attach event listeners to change user status dynamically
	if (onlineEl && invisibleEl) {
		onlineEl.addEventListener("click", () => updateUserStatus("active"));
		invisibleEl.addEventListener("click", () => updateUserStatus("inactive"));
	}
	//   change right side display to Block
	rightSideNav.style.display = "block";

	// Mark the user as online sitewide (not just on the Messages page) so that
	// presence dots elsewhere (e.g. Manage Candidates) reflect reality.
	startPresenceSocket();
};


// ---- Sitewide presence WebSocket ----
// Opens a single connection to the messaging consumer on any authenticated
// page so Messaging.UserProfile.is_online stays true while the user is active.
// The Messages page opens its own socket, so we skip it there to avoid a
// duplicate connection.
let _presenceSocket = null;
let _presenceReconnectDelay = 1000;
const _PRESENCE_MAX_DELAY = 30000;

// Increment (or adjust) the header unread-messages badge (#notification-count)
// in real time. Clamps at 0 and hides the badge when empty.
function bumpHeaderMessageCount(delta = 1) {
	const badge = document.getElementById("notification-count");
	if (!badge) return;
	const current = parseInt(badge.textContent, 10) || 0;
	const next = Math.max(0, current + delta);
	badge.textContent = next;
	badge.style.display = next > 0 ? "" : "none";
}

async function startPresenceSocket() {
	if (window.location.pathname.startsWith("/dashboard/messages")) return; // page owns its socket
	if (_presenceSocket &&
		(_presenceSocket.readyState === WebSocket.OPEN ||
		 _presenceSocket.readyState === WebSocket.CONNECTING)) {
		return; // already connected/connecting
	}

	// Need a valid access token; refresh if necessary.
	if (!(await isAuthenticated()) || !accessToken) return;

	const scheme = window.location.protocol === "https:" ? "wss" : "ws";
	const url = `${scheme}://${window.location.host}/ws/messaging/?token=${encodeURIComponent(accessToken)}`;

	try {
		_presenceSocket = new WebSocket(url);
	} catch (err) {
		console.error("Presence socket failed to open:", err);
		return;
	}

	_presenceSocket.onopen = () => { _presenceReconnectDelay = 1000; };

	// Keep the header unread-messages badge live on every authenticated page.
	// The backend pushes a `send_notification` event (Messaging/signals.py) to
	// the recipient's user group whenever a new Message is created.
	_presenceSocket.onmessage = (event) => {
		let data;
		try { data = JSON.parse(event.data); } catch (e) { return; }
		if (data.type === "send_notification") {
			// The notification row is already persisted before this event is
			// sent, so an authoritative refresh of the dropdown + badge is
			// race-free. Fall back to a simple bump on pages that only have the
			// badge (no notification dropdown / renderUnread).
			if (typeof renderUnread === "function") {
				renderUnread();
			} else {
				bumpHeaderMessageCount(1);
			}
		}
	};

	_presenceSocket.onclose = () => {
		_presenceSocket = null;
		// Don't reconnect if we're navigating away.
		if (document.visibilityState === "hidden") return;
		setTimeout(startPresenceSocket, _presenceReconnectDelay);
		_presenceReconnectDelay = Math.min(_presenceReconnectDelay * 2, _PRESENCE_MAX_DELAY);
	};

	_presenceSocket.onerror = () => {
		try { _presenceSocket && _presenceSocket.close(); } catch (e) {}
	};
}

// Close cleanly on navigation/unload so the consumer marks the user offline.
window.addEventListener("beforeunload", () => {
	if (_presenceSocket) {
		try { _presenceSocket.close(); } catch (e) {}
		_presenceSocket = null;
	}
});


// ---- Helper: update user status ----
async function updateUserStatus(newStatus) {
	try {
		const response = await fetchProtected("/api/users/status/", {
			method: "PATCH",
			headers: {
			},
			body: JSON.stringify({ status: newStatus }),
		});

		if (response.ok) {
			userInfo.status = newStatus;
			console.log(`Status updated to ${newStatus}`);
			// Reflect UI change
			const indicator = document.querySelector(".status-indicator");
			const onlineEl = document.querySelector(".user-online");
			const invisibleEl = document.querySelector(".user-invisible");
			if (newStatus === "inactive") {
				indicator.classList.add("right");
				onlineEl.classList.remove("current-status");
				invisibleEl.classList.add("current-status");
				document.querySelectorAll(".user-avatar").forEach(el => {
					el.classList.remove("status-online");
					el.classList.add("status-invisible");
				});
			} else {
				indicator.classList.remove("right");
				onlineEl.classList.add("current-status");
				invisibleEl.classList.remove("current-status");
				document.querySelectorAll(".user-avatar").forEach(el => {
					el.classList.remove("status-invisible");
					el.classList.add("status-online");
				});
			}
		} else {
			console.error("Failed to update status");
		}
	} catch (err) {
		console.error("Error updating status:", err);
	}
}

// ---- Helper: check authentication (already partly defined in your code) ----
let _authPromise = null;
async function isAuthenticated() {
	if (accessToken && !isTokenExpired(accessToken)) {
		userInfo = decodeJwtPayload(accessToken);
		return true;
	}
	if (_authPromise) return _authPromise;
	_authPromise = (async () => {
		try {
			const res = await fetch("/api/auth/token/refresh/", {
				method: "POST",
				credentials: "include",
			});
			if (res.ok) {
				const data = await res.json();
				accessToken = data.access;
				userInfo = decodeJwtPayload(accessToken);
				return true;
			}
			return false;
		} catch (err) {
			console.error("Authentication check failed:", err);
			return false;
		} finally {
			_authPromise = null;
		}
	})();
	return _authPromise;
}

// Send guests to login, returning them to this page after they sign in.
// Returns true when the visitor is authenticated (caller may proceed).
async function requireLogin() {
	if (await isAuthenticated()) return true;
	const here = window.location.pathname + window.location.search;
	window.location.href = `/login/?redirect=${encodeURIComponent(here)}`;
	return false;
}

// Append error message to login form
function appendError(error, errorType = "error", elementId = "page-error-container") {
	const errorContainer = document.getElementById(elementId);
	const errDiv = document.createElement('div');
	errDiv.innerHTML = `
    <div class="notification ${errorType} closeable">
				<p>${error}</p>
				<a class="close" href=""></a>
			</div>`;
	errorContainer.appendChild(errDiv);

	setTimeout(() => {
		errDiv.remove();
	}, 5000);
}

// Show loading overlay
function showLoading(message = null) {
	if (message !== null) {
		document.getElementById('my-pop-up').textContent = message;
	}
	document.getElementById('loadingOverlay').classList.add('active');
}

// Hide loading overlay
function hideLoading() {
	document.getElementById('loadingOverlay').classList.remove('active');
}

// Base function to check subscription for any feature
async function checkSubscription(featureName) {
	try {
		const response = await fetchProtected(`/api/pricing/subscription/check/?feature=${featureName}`, {});

		if (!response.ok) {
			return {
				allowed: false,
				message: "Unable to check subscription right now."
			};
		}

		return await response.json();
	} catch (error) {
		console.error("Subscription Check Error:", error);
		return {
			allowed: false,
			message: "Network error. Please try again."
		};
	}
}


// Helper to handle the logic for any button
async function handleFeatureAction(featureName, callbackAction) {
	const result = await checkSubscription(featureName);

	if (!result.allowed) {
		alert(result.message || "Your subscription does not allow this feature.");

		if (result.message && result.message.includes("No active subscription")) {
			content = `<h2>No Active Subscription</h2>
			<p>You do not have an active subscription plan that includes access to the <strong>${featureName.replace(/-_/g, " ").toUpperCase()}</strong> feature. Please subscribe to a plan to gain access.</p>`;
			showOverAllPopup(content, "View Pricing Plans", "/pricing-plans/");
			return;
		}
		content = `<h2>Upgrade Your Plan</h2>
		<p>Your current subscription plan does not include access to the <strong>${featureName.replace(/-_/g, " ").toUpperCase()}</strong> feature. Please upgrade your plan to gain access.</p>`;
		showOverAllPopup(content, "View Pricing Plans", "/pricing-plans/");
		return;
	}
	callbackAction();
}

function initiateFeatureCheck(buttonId, featureName, realAction) {

	document.getElementById(buttonId).addEventListener("click", async function () {
		if (!await isAuthenticated()) {
			content = `<h2>Log In To Access</h2>
			<p>You need to be logged in to access the <strong>${featureName.replace(/-_/g, " ").toUpperCase()}</strong> feature. 
			Please log in or register an account.</p>`;

			const currentUrl = window.location.href;
			const queryString = currentUrl.split('/').slice(3).join('/');
			const newUrl = "/login" + '?redirect=/' + queryString;

			showOverAllPopup(content, "Log In / Register", newUrl);
			return;
		}
		handleFeatureAction(featureName, () => {
			// REAL ACTION: Open job posting modal or redirect to job form
			// window.location.href = "/jobs/create/";
			realAction();
		});
	});

}

function showOverAllPopup(content, actionText, url) {
	const overlay = document.getElementById("overall-overlay");
	const popup = document.getElementById("overall-popup");
	const popupContent = document.querySelector(".overall-popup-content");
	const actionBtn = document.getElementById("overall-complete-btn");

	overlay.classList.add("active");
	popup.classList.add("active");

	// Popup content
	popupContent.querySelector("div").innerHTML = content;

	// Button action
	actionBtn.innerHTML = actionText;

	actionBtn.onclick = () => {
		window.location.href = url;
	};

	// Clicking overlay closes popup
	overlay.onclick = () => {
		overlay.classList.remove("active");
		popup.classList.remove("active");
	};
}

$(document).on('click', '.mfp-trigger', function (e) {
	e.preventDefault();

	const target = $(this).data('mfp-src'); // popup ID

	$.magnificPopup.open({
		items: {
			src: target
		},
		type: 'inline',
		midClick: true
	});
});

function disableButton(button, btnText, profileUserId) {
	// disable the apply button if the user is viewing their own profile
	if (userInfo && userInfo.id === profileUserId) {
		// 1. Add a 'disabled' class for CSS styling
		button.classList.add('button-disabled');

		// 2. Prevent the popup from opening
		button.style.pointerEvents = 'none';
		button.style.opacity = '0.5';

		// 3. Optional: Change the text
		button.innerHTML = btnText + ' <i class="icon-material-outline-lock"></i>';
	}
}
