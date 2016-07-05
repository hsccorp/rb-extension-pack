/*
 * Class for providing a view onto a PDF document.
 *
 * This handles the common functionality, such as loading the pdf, determining
 * the commentable region, rendering, and so on.
 *
 * This view displays the PDF documents using pdf.js and allows it to be 
 * commented on.
 */
PDFAttachmentView = Backbone.View.extend({
    mode: 'attachment',
    name: null,
    tagName: 'pdf',

    /*
     * Initializes the view.
     */
    initialize: function() {
        this.$commentRegion = null;
    },


    /*
     * Renders the view.
     *
     * This will by default render the template into the element and begin
     * loading images.
     */
    render: function(pdfUrl, topLevelDiv) {

        PDFJS.getDocument(pdfUrl).then(function(pdf) {

            var scale = 1.5;

            for (var i = 1; i <= pdf.numPages; i++) {
                pdf.getPage(i).then(function handlePage(page){
                    var viewport = page.getViewport(scale);
                    var pageDiv = document.createElement('div');
                    pageDiv.id = 'pdfdiv' + page.pageIndex;
                    pageDiv.className = 'pdfdiv';
                    pageDiv.style["text-align"] = "center";                  // TBD: move it to css file
                    topLevelDiv.append(pageDiv);

                    var canvas = document.createElement('canvas');
                    canvas.className = 'pdfcanvas';
                    canvas.id = 'pdfcanvas' + page.pageIndex;
                    canvas.style.border = '1px solid black';   // TBD: move it to css

                    var context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                
                    //Draw it on the canvas
                    page.render({canvasContext: context, viewport: viewport});
                
                    //Add it to the parent div
                    pageDiv.appendChild(canvas);
                });
            }
        });


    /*    $("canvas").on("mousedown", function(){
            console.log('md');
        });

        $("canvas").on("mouseup", function(){
            console.log('mu');
        });
*/
        // Set the commentRegion
        this.$commentRegion = this.$el; //TBD: is this OK?
        this.$commentRegion = topLevelDiv;

        return this;
    },

    /*
     * Returns the region of the view where commenting can take place.
     *
     * The region is based on the $commentRegion member variable, which must
     * be set by a subclass.
     */
    getSelectionRegion: function() {
        var $region = this.$commentRegion,
            offset = $region.position();

        /*
         * The margin: 0 auto means that position.left() will return
         * the left-most part of the entire block, rather than the actual
         * position of the region on Chrome. Every other browser returns 0
         * for this margin, as we'd expect. So, just play it safe and
         * offset by the margin-left. (Bug #1050)
         */
        offset.left += $region.getExtents('m', 'l');

        return {
            left: offset.left,
            top: offset.top,
            width: $region.width(),
            height: $region.height()
        };
    }
});



PDFReviewableView = RB.FileAttachmentReviewableView.extend({
    className: 'pdfreview-review-ui',

    commentBlockView: RB.RegionCommentBlockView,

    events: {
        'mousedown .selection-container': '_onMouseDown',
        'mouseup .selection-container': '_onMouseUp',
        'mousemove .selection-container': '_onMouseMove'
    },

    /*
     * Initializes the view.
     */
    initialize: function(options) {
        RB.FileAttachmentReviewableView.prototype.initialize.call(
            this, options);

        _.bindAll(this, '_adjustPos');

        this._activeSelection = {};

        /*
         * Add any CommentBlockViews to the selection area when they're
         * created.
         */
        this.on('commentBlockViewAdded', function(commentBlockView) {
            commentBlockView.setSelectionRegionSizeFunc(_.bind(function() {
                var region = this._view.getSelectionRegion();

                return {
                    width: region.width,
                    height: region.height
                };
            }, this));

            this._$selectionArea.append(commentBlockView.$el);
        }, this);
    },

    /*
     * Renders the view.
     *
     * This will set up a selection area over the image and create a
     * selection rectangle that will be shown when dragging.
     *
     * Any time the window resizes, the comment positions will be adjusted.
     */
    renderContent: function() {
        var self = this,
            captionItems = [],
            $header;

        this._$selectionArea = $('<div/>')
            .addClass('selection-container')
            .hide()
            .proxyTouchEvents();

        this._$selectionRect = $('<div/>')
            .addClass('selection-rect')
            .prependTo(this._$selectionArea)
            .proxyTouchEvents()
            .hide();

        this.$el
            /*
             * Register a hover event to hide the comments when the mouse
             * is not over the comment area.
             */
            .hover(
                function() {
                    self._$selectionArea.show();
                    self._adjustPos();
                },
                function() {
                    if (self._$selectionRect.is(':hidden') &&
                        !self.commentDlg) {
                        self._$selectionArea.hide();
                    }
                })
            .append(this._$selectionArea);

        this._view = new PDFAttachmentView({
            model: this.model
        });

        this._view.$el.appendTo(this.$el);
        this._view.render(this.model.get('pdfURL'), this.$el);

        /*
         * Reposition the selection area on page resize or loaded, so that
         * comments are in the right locations.
         */
        $(window)
            .resize(this._adjustPos)
            .load(this._adjustPos);

        $header = $('<div />')
            .addClass('review-ui-header')
            .prependTo(this.$el);

        if (this.model.get('numRevisions') > 1) {
            $revisionLabel = $('<div id="revision_label" />')
                .appendTo($header);
            this._revisionLabelView = new RB.FileAttachmentRevisionLabelView({
                el: $revisionLabel,
                model: this.model
            });
            this._revisionLabelView.render();
            this.listenTo(this._revisionLabelView, 'revisionSelected',
                          this._onRevisionSelected);

            $revisionSelector = $('<div id="attachment_revision_selector" />')
                .appendTo($header);
            this._revisionSelectorView = new RB.FileAttachmentRevisionSelectorView({
                el: $revisionSelector,
                model: this.model
            });
            this._revisionSelectorView.render();
            this.listenTo(this._revisionSelectorView, 'revisionSelected',
                          this._onRevisionSelected);

            if (!this.renderedInline) {
                captionItems.push(this.captionItemTemplate({
                    caption: interpolate(
                        gettext('%(caption)s (revision %(revision)s)'),
                        {
                            caption: this.model.get('caption'),
                            revision: this.model.get('fileRevision')
                        },
                        true)
                }));

                $header.append(this.captionTableTemplate({
                    items: captionItems.join('')
                }));
            }
        } else {
            if (!this.renderedInline) {
                $('<h1 />')
                    .addClass('caption')
                    .text(this.model.get('caption'))
                    .appendTo($header);
            }
        }

        return this;
    },

    /*
     * Callback for when a new file revision is selected.
     *
     * This supports single revisions and diffs. If 'base' is 0, a
     * single revision is selected, If not, the diff between `base` and
     * `tip` will be shown.
     */
    _onRevisionSelected: function(revisions) {
        var revisionIDs = this.model.get('attachmentRevisionIDs'),
            base = revisions[0],
            tip = revisions[1],
            revisionBase,
            revisionTip,
            redirectURL;

        // Ignore clicks on No Diff Label
        if (tip === 0) {
            return;
        }

        revisionTip = revisionIDs[tip-1];

        /* Eventually these hard redirects will use a router
         * (see diffViewerPageView.js for example)
         * this.router.navigate(base + '-' + tip + '/', {trigger: true});
         */

        if (base === 0) {
            redirectURL = '../' + revisionTip + '/';
        } else {
            revisionBase = revisionIDs[base-1];
            redirectURL = '../' + revisionBase + '-' + revisionTip + '/';
        }
        window.location.replace(redirectURL);
    },


    /*
     * Handles a mousedown on the selection area.
     *
     * If this is the first mouse button, and it's not being placed on
     * an existing comment block, then this will begin the creation of a new
     * comment block starting at the mousedown coordinates.
     */
    _onMouseDown: function(evt) {
        console.log("_onMouseDown");
        if (evt.which === 1 &&
            !this.commentDlg &&
            !$(evt.target).hasClass('selection-flag')) {
            var offset = this._$selectionArea.offset();

            this._activeSelection.beginX =
                evt.pageX - Math.floor(offset.left) - 1;
            this._activeSelection.beginY =
                evt.pageY - Math.floor(offset.top) - 1;

            this._$selectionRect
                .move(this._activeSelection.beginX,
                      this._activeSelection.beginY)
                .width(1)
                .height(1)
                .show();

            if (this._$selectionRect.is(':hidden')) {
                this.commentDlg.close();
            }

            return false;
        }
    },

    /*
     * Handles a mouseup on the selection area.
     *
     * This will finalize the creation of a comment block and pop up the
     * comment dialog.
     */
    _onMouseUp: function(evt) {
        console.log("_onMouseUp");
        if (!this.commentDlg &&
            this._$selectionRect.is(":visible")) {
            var width = this._$selectionRect.width(),
                height = this._$selectionRect.height(),
                offset = this._$selectionRect.position();

            evt.stopPropagation();
            this._$selectionRect.hide();

            /*
             * If we don't pass an arbitrary minimum size threshold,
             * don't do anything. This helps avoid making people mad
             * if they accidentally click on the image.
             */
            if (width > 5 && height > 5) {
                this.createAndEditCommentBlock({
                    x: Math.floor(offset.left),
                    y: Math.floor(offset.top),
                    width: width,
                    height: height
                });
            }
        }
    },

    /*
     * Handles a mousemove on the selection area.
     *
     * If we're creating a comment block, this will update the
     * size/position of the block.
     */
    _onMouseMove: function(evt) {
        console.log("_onMouseMove");
        if (!this.commentDlg && this._$selectionRect.is(":visible")) {
            var offset = this._$selectionArea.offset(),
                x = evt.pageX - Math.floor(offset.left) - 1,
                y = evt.pageY - Math.floor(offset.top) - 1;

            this._$selectionRect
                .css(this._activeSelection.beginX <= x
                     ? {
                           left:  this._activeSelection.beginX,
                           width: x - this._activeSelection.beginX
                       }
                     : {
                           left:  x,
                           width: this._activeSelection.beginX - x
                       })
                .css(this._activeSelection.beginY <= y
                     ? {
                           top:    this._activeSelection.beginY,
                           height: y - this._activeSelection.beginY
                       }
                     : {
                           top:    y,
                           height: this._activeSelection.beginY - y
                       });

            return false;
        }
    },

    /*
     * Reposition the selection area to the right locations.
     */
    _adjustPos: function() {
        var region = this._view.getSelectionRegion();

        this._$selectionArea
            .width(region.width)
            .height(region.height)
            .css({
                left: region.left,
                top: region.top
            });
    }
});

