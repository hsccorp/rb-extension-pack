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
     * loading the document.
     */
    render: function(pdfUrl, topLevelDiv) {

        PDFJS.disableWorker = true;
        PDFJS.workerSrc = '/static/ext/pdfreview.extension.PDFReviewUIExtension/js/lib/pdf.worker.js';
        PDFJS.getDocument(pdfUrl).then(function(pdf) {
            /*
             * The page is scaled by a factor of 1.5 before being rendered.
             * This makes it look better. With a 1:1 scaling, the user would
             * want to zoom in. With the zoom feature not provided right now
             * a default scaling seems better option.
             *
             * NOTE: The same scaling is used at the backend to create
             * thumbnails for the regions where reviewer has provided comments.
             * If changing this scale, do change the scale at backend too i.e.
             * in extension.py file.
             */
            var scale = 1.5;

            /*
             * Each page of the PDF document is rendered in one canvas element.
             * Each canvas element resides in a div. All these divs are
             * appended to the topLevelDiv.
             */

            /*
             * First create all the required divs and append them to the
             * topLevelDiv. This is done beforehand so that when the PDF
             * pages are fetched asynchronously, they can be added to the
             * respective parent div. The pdf.getPage being async, can provide
             * pages out of order. */
            for (var i = 0; i < pdf.numPages; i++) {
                var pageDiv = document.createElement('div');
                pageDiv.id = 'pdfdiv' + i;
                pageDiv.className = 'pdfdiv';
                topLevelDiv.append(pageDiv);
            }

            for (var i = 1; i <= pdf.numPages; i++) {
                pdf.getPage(i).then(function handlePage(page){
                    var viewport = page.getViewport(scale);

                    var canvas = document.createElement('canvas');
                    canvas.className = 'pdfcanvas';
                    canvas.id = 'pdfcanvas' + page.pageIndex;
                    var context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;

                    //Draw it on the canvas
                    page.render({canvasContext: context, viewport: viewport});

                    //Add it to the corresponding parent div
                    $("#pdfdiv" + page.pageIndex)[0].appendChild(canvas);
                });
            }

            /* Populate the page selector */
            for(var i = 1; i <= pdf.numPages; i++)
            {
                var pageId = i.toString();
                $(".page-selector").append($("<option/>").attr("value", pageId).text(pageId));
            }

        });

        // Set the commentRegion
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

        /*this sets the selection region with respect to first page canvas
         */

        var allPages = $(".pdfcanvas"),firstPage = $("#pdfcanvas0"),lastPage = $("#pdfcanvas"+(allPages.length - 1));
        return {
                 left: firstPage.position().left,
                 top: firstPage.position().top,
                 width: firstPage.width(),
                 height: lastPage.position().top + lastPage.height() - firstPage.position().top
               };
        }
});



/*
 * Displays a review UI for PDF documents.
 *
 * This supports reviewing individual PDF documents only. The document will
 * be displayed, centered, and all existing comments will be shown as selection
 * boxes on top of it. Users can click and drag across the PDF document to
 * leave a comment on that area.
 *
 * In case the document has multiple revisions, it also presents a dropdown to
 * choose a revision to view.
 */
PDFReviewableView = RB.FileAttachmentReviewableView.extend({
    className: 'pdfreview-review-ui',

    commentBlockView: RB.RegionCommentBlockView,

    events: {
        'mousedown .selection-container': '_onMouseDown',
        'mouseup .selection-container': '_onMouseUp',
        'mousemove .selection-container': '_onMouseMove'
    },

    captionItemTemplate: _.template([
         '<td>',
          ' <h1 class="caption">',
          '  <%- caption %>',
          ' </h1>',
          '</td>'
    ].join('')),

    captionTableTemplate: _.template(
         '<table><tr><%= items %></tr></table>'
    ),


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
     * This will set up a selection area over the PDF document and create a
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

        var actionBarDiv = document.createElement('div');
        actionBarDiv.className = "pdf-revision-selector-div";
        ($header).append(actionBarDiv);
        /*
         * When the document has multiple revisions, show a dropdown to view
         * different revisions.
         */
        var numRevisions = this.model.get('numRevisions');
        if (numRevisions > 1) {
            var revisionIDs = this.model.get('attachmentRevisionIDs');

            var label = $("<label>").text('Choose the revision');
            label.attr("class","pdf-revision-selector-label");
            label.appendTo(actionBarDiv);

            var choices = [];
            for(var i = 1; i <= numRevisions; i++)
            {
                choices.push(i.toString());
            }

            /*here select option  allows us to create a drop down
             *to choose our revision document
            */

            var select = $("<select/>");
            $.each(choices, function(a, b) {
                select.append($("<option/>").attr("value", b).text(b));
            });

            select.val(this.model.get('fileRevision')).change();
            select.attr("class", "pdf-revision-selector");
            select.appendTo(actionBarDiv);

            /* Add a listener for the dropdown */
            select.on("change", function (e) {
                console.log("x");
                var selectedRevision = revisionIDs[this.selectedIndex],
                    redirectURL = '../' + selectedRevision + '/';
                window.location.replace(redirectURL);
            });

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

        /* Add a page selector */
        var select = $("<select/>");
        select.attr("class", "page-selector");
        select.appendTo(actionBarDiv);

        var label = $("<label>").text('Jump to page');
        label.attr("class","page-selector-label");
        label.appendTo(actionBarDiv);

        /* Add a listener for the dropdown */
        select.on("change", function (e) {
            var targetDiv = "#pdfdiv" + this.selectedIndex;
            $(targetDiv)[0].scrollIntoView({block: "top"})
        });

        return this;
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
             * if they accidentally click on the document.
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

