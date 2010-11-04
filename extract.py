////////////////////////////////////////////////////////////////////////////////
// Extract content from HTML (if URL is not feed or explicit HTML request has been made)
////////////////////////////////////////////////////////////////////////////////

if ($html_only || !$result) {
   $html = @file_get_contents($url);
  if (!$html) die('Error retrieving '.$url);
  $html = convert_to_utf8($html, $http_response_header);
  // Run through Tidy (if it exists).
  // This fixes problems with some sites which would otherwise
  // trouble DOMDocument HTML parsing.
  if (function_exists('tidy_parse_string')) {
      $tidy = tidy_parse_string($html, $tidy_config, 'UTF8');
      if (tidy_clean_repair($tidy)) {
	  $html = $tidy->value;
      }
  }
  $readability = new Readability($html, $url);
  if ($links == 'footnotes')
      $readability->convertLinksToFootnotes = true;
   $readability->init();
   $readability->clean($readability->getContent(), 'select');
   if ($options->rewrite_relative_urls)
       makeAbsolute($url, $readability->getContent());
   $title = $readability->getTitle()->textContent;
   $content = $readability->getContent()->innerHTML;
   if ($links == 'remove') {
       $content = preg_replace('!</?a[^>]*>!', '', $content);
   }
   if (!$valid_key) {
       $content = $options->message_to_prepend.$content;
       $content .= $options->message_to_append;
   } else {
       $content = $options->message_to_prepend_with_key.$content;
       $content .= $options->message_to_append_with_key;
   }
 
