---
title: How to test saved web pages offline
seo_title: Test saved web pages offline | Browse Awesome
description: >-
  To test a saved web page offline, open the saved artifact in a fresh browser
  context without network access, then check the text and images you need.
  Do not reopen the original URL. A successful capture check establishes that
  copy's readability; it does not prove that a bookmark manager's backup can
  restore your library.
meta_description: Test saved web pages offline with a reusable sample page, a worked capture experiment, and checks that separate snapshots from bookmark backups.
published_at: 2026-10-15T01:25:00+03:00
updated_at: 2026-10-15T01:25:00+03:00
author: Browse Awesome editorial team
author_type: Organization
image: /static/brand/awesome-repos-social.png
image_alt: Browse Awesome repository discovery
categories:
  - Repository evaluation
tags:
  - Web archiving
  - Self-hosted software
keywords:
  - test saved web pages offline
  - bookmark archive verification
---

A bookmark can still open perfectly while its supposed archive is incomplete. The browser may be showing the original page, or loading an image that never made it into the saved copy. You discover the difference when the source disappears.

Browse Awesome ran a controlled capture experiment on October 14, 2026, UTC. A plain HTML control retained the sample sentence but could not load its image offline. A SingleFile capture retained both. You can use the same [archive test page](/static/archive-test/page.html) to check your own capture workflow before trusting it with important material.

This is a narrow acceptance test, not a ranking of bookmarking products. Start with a candidate from the [self-hosted repository list](/lists/awesome-selfhosted/), decide what you need to preserve, and test that requirement. For broader maintenance and suitability checks, use the [repository-shortlisting guide](/blog/how-to-shortlist-github-repositories/).

1. Identify the content that must survive.
2. Save it and record the capture method.
3. Open the artifact without access to the original site.
4. Test recovery separately from capture.

## 1. Choose what must survive

Write down a concrete requirement before clicking Save. “Keep this article” could mean readable text, the original layout, a diagram, an attached PDF, or a functioning interactive example. Those are different promises. A readable-text archive can satisfy the first and fail the others without being broken.

For the sample page, require the sentence **“The copper heron keeps a paper map.”** and the actual image showing a green circle, a blue square, and “Saved together.” The image is a separate resource, so it tests something that the sentence alone cannot. Seeing its alternative text does not count as seeing the image.

The sample also links to another document. Treat that as a boundary check: saving one page does not establish that you saved the destinations of its links. If your work requires a linked PDF, make that file a separate requirement and verify its saved copy too.

Keep the first trial public and non-sensitive. The supplied fixture contains no account data. Once the procedure works, repeat it on a representative page you are authorized to save. Do not publish personal captures or upload a private bookmark export to demonstrate the result.

## 2. Save the page and record the capture

Open the [test page](/static/archive-test/page.html) while online and confirm that the image is visible. Use the capture method you actually intend to rely on. Record the tool and version, relevant settings, capture time, source address, and where the resulting file lives. These notes make a later failure reproducible. Keep a short result beside them: required content; artifact opened; network isolation used; observed omissions; pass, fail, or inconclusive. Keep the capture result separate from any later recovery result.

Wait for capture to finish. A bookmark appearing in a list may mean only that the URL was saved. In a bookmarking application, locate the preserved representation or its download control rather than assuming the bookmark's normal Open action uses it. For example, [Linkwarden's preservation documentation](https://docs.linkwarden.app/usage/preservation) distinguishes preserved formats from the original page and describes capture as queued work.

For a standalone HTML workflow, [SingleFile](https://github.com/gildas-lormeau/SingleFile) is one available capture tool. Its [FAQ](https://github.com/gildas-lormeau/SingleFile/blob/main/faq.md) explains that scripts are removed by default. Therefore, a button that no longer performs its live action is not by itself evidence that the visible content was lost. Decide whether that action belongs in your requirement.

Keep the original capture unchanged during diagnosis. Do not use a bookmark manager's Refresh command as a harmless inspection step: Linkwarden documents that refreshing preserved formats deletes existing copies before fetching the live page again. If the old source matters, inspect or download the existing copy first.

## 3. Reopen without the original site

Test the saved artifact, not a shortcut to its source. For a downloaded HTML file, use a fresh browser profile or another clean browser environment that has not loaded the original page. Disconnect that environment from the network before opening the file. A fresh context matters because previously cached resources can make an incomplete capture look complete.

Find the sample sentence in the saved document and try selecting its text. Inspect the actual image, including its shapes and label. If an image is missing, record that result rather than accepting the surrounding caption as a substitute. Check the browser's address: reopening the live source is a different operation.

If your archive is served by a self-hosted application, disconnecting everything also disconnects the archive server. That failure tells you nothing about capture quality. Either download the preserved artifact and test it locally, or use an isolated test setup that can reach the archive server but cannot reach the original site or its asset hosts. Do not change production networking merely to run this check.

Report only what you observed. “Text and the required diagram opened without the source” is useful. “This saves every website” is not. If a required element fails, preserve the failed sample, investigate the capture settings, and retry while the source remains available. If you could not isolate the network or identify the saved artifact, mark the test inconclusive.

## Worked example: an image exposes a missing dependency

Browse Awesome's experiment used fixture version 1, Chromium 153.0.8010.12, Playwright 1.64.1, and the SingleFile library bundled with `single-file-cli` 2.18.3. The fixture was served through an intercepted test origin. Its text was in the HTML; its SVG image was a separate file. There was no authentication, lazy loading, video, or application database.

The control copied the page's DOM HTML and retained a base URL pointing to that origin. It deliberately did **not** package the image. This is not a test of a browser's “Save complete page” command, and it should not be read as one. The capture used SingleFile's library with scripts removed and HTML compression disabled, following its [Playwright integration approach](https://github.com/gildas-lormeau/SingleFile/wiki/Executing-within-Playwright-%28headless-browser%29), adapted to that installed version.

Both outputs were reopened as HTML data documents in separate fresh, offline browser contexts with service workers blocked. This was automated isolated replay, not a local-file browser-menu test. The checks inspected visible text and whether the image had decoded, then captured screenshots.

| Artifact | Sample sentence | Required image | What this establishes |
|---|---|---|---|
| DOM HTML control | Present | Missing; request failed offline | Text alone can conceal an external dependency |
| SingleFile snapshot | Present | Loaded from embedded image data | This capture retained the required content without its source |

The snapshot still pointed its separate-document link at the test origin. The experiment did not demonstrate preservation of that destination. It also did not test a bookmark manager, an account export, a restored server, arbitrary websites, or comparative reliability. The useful result is the repeatable failure check, not a product winner.

## 4. Check recovery separately

After capture passes, ask where the surviving copy will come from if your usual device or server is lost. Keeping a readable artifact beside the application that produced it does not answer that question. Retain an independent copy, reopen it in a clean location, and check the same required content. A copied HTML file tests file recovery only.

For a bookmark application, use its documented backup and restore procedure on a disposable destination. Verify that the restored application can find the saved item and open its preserved content. Include the database and storage required by that deployment; restoring URLs into an empty library is not equivalent to restoring the old page snapshots.

The distinction is concrete in current documentation. [linkding's backup guide](https://linkding.link/backups/) says its UI export omits HTML snapshots, and copying the assets directory back after importing that export does not reconnect them. [Linkwarden's import/export guide](https://docs.linkwarden.app/usage/import-and-export) says its JSON export excludes preserved files; importing it regenerates those files rather than transferring the old copies. Regeneration depends on what can be fetched then.

Neither application was installed or restored for this article. Those are documentation-backed reasons to rehearse recovery, not measured failures. Keep capture, portability, and full recovery as separate entries in your evaluation notes. If you are still choosing software, [search the repository catalog for bookmark projects](/repos/?q=bookmark) and take each candidate's current upstream instructions into the trial.

## Common questions

### Does saving a bookmark save the page?

Not necessarily. A bookmark can store only the original URL. Check whether your chosen tool also captures the page content, and test the saved result without access to the original site.

### Does an offline copy prove that my backups work?

No. Opening a saved page tests that capture. Backup recovery is a separate test: restore a copy into a clean location or instance, then check that you can find and open it.

### Should every part of a saved page work offline?

Only if that is part of your requirement. Text, images, downloadable files, links, and interactive features have different dependencies. Record what must survive before testing, and report missing behavior instead of assuming it was captured.
