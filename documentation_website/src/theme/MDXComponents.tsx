import React from 'react';
import MDXComponents from '@theme-original/MDXComponents';
import ZoomImage from '@site/src/components/ZoomImage';

export default {
  ...MDXComponents,
  ZoomImage,
  // If we want to replace all markdown images with ZoomImage:
  // img: (props) => <ZoomImage {...props} />
};
