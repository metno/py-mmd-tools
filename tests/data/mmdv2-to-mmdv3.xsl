<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:gco="http://www.isotc211.org/2005/gco"
    xmlns:gmd="http://www.isotc211.org/2005/gmd"
    xmlns:gml="http://www.opengis.net/gml"
    xmlns:mmd="http://www.met.no/schema/mmd"
    xmlns="http://www.met.no/schema/mmd"
    xmlns:date="http://exslt.org/dates-and-times"
    version="1.0">

    <xsl:output method="xml" encoding="UTF-8" indent="yes" />
    <xsl:strip-space elements="*"/>

    <xsl:template match="/mmd:mmd">
        <xsl:element name="mmd:mmd">

            <xsl:apply-templates select="mmd:metadata_identifier" />
            <xsl:apply-templates select="mmd:title" />
            <xsl:apply-templates select="mmd:abstract" />
            <xsl:apply-templates select="mmd:metadata_status" />
            <xsl:apply-templates select="mmd:dataset_production_status" />
            <xsl:apply-templates select="mmd:collection" />
            <xsl:apply-templates select="mmd:last_metadata_update" />
            <xsl:apply-templates select="mmd:temporal_extent" />
            <xsl:apply-templates select="mmd:iso_topic_category" />
            <xsl:apply-templates select="mmd:keywords" />
            <xsl:apply-templates select="mmd:operational_status" />
            <xsl:apply-templates select="mmd:dataset_language" />
            <xsl:apply-templates select="mmd:access_constraint" />
            <xsl:apply-templates select="mmd:use_constraint" />
            <xsl:apply-templates select="mmd:project" />
            <xsl:apply-templates select="mmd:activity_type" />
            <xsl:apply-templates select="mmd:platform" />
            <xsl:apply-templates select="mmd:related_information" />
	    <xsl:apply-templates select="mmd:personnel"/>
	    <xsl:apply-templates select="mmd:dataset_citation"/>
            <xsl:apply-templates select="mmd:data_access" />
            <xsl:apply-templates select="mmd:data_center" />
            <xsl:apply-templates select="mmd:related_dataset" />
            <xsl:apply-templates select="mmd:geographic_extent/mmd:rectangle" />
            <xsl:apply-templates select="mmd:geographic_extent/mmd:polygon" />
            <xsl:apply-templates select="mmd:system_specific_product_category" />
            <xsl:apply-templates select="mmd:system_specific_product_relevance" />

        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:metadata_identifier">
      <xsl:element name="mmd:metadata_identifier">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:title">
      <xsl:element name="mmd:title">
	  <xsl:attribute name="xml:lang">
             <xsl:value-of select="@xml:lang" />
	  </xsl:attribute>
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:abstract">
      <xsl:element name="mmd:abstract">
	  <xsl:attribute name="xml:lang">
             <xsl:value-of select="@xml:lang" />
	  </xsl:attribute>
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:metadata_status">
      <xsl:element name="mmd:metadata_status">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:dataset_production_status">
      <xsl:element name="mmd:dataset_production_status">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:collection">
      <xsl:element name="mmd:collection">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:last_metadata_update">
      <xsl:element name="mmd:last_metadata_update">
      <xsl:element name="mmd:update">
         <xsl:element name="mmd:datetime">
            <xsl:value-of select="." />
         </xsl:element>
         <xsl:element name="mmd:type">
            <xsl:text>Created</xsl:text>
         </xsl:element>
      </xsl:element>
      <xsl:element name="mmd:update">
        <xsl:element name="mmd:datetime">
            <xsl:value-of select="date:date-time()"/>
        </xsl:element>
         <xsl:element name="mmd:type">
            <xsl:text>Minor modification</xsl:text>
         </xsl:element>
         <xsl:element name="mmd:note">
            <xsl:text>Change version of metadata standard to MMD v3</xsl:text>
         </xsl:element>
      </xsl:element>
      </xsl:element>
    </xsl:template>


    <xsl:template match="mmd:temporal_extent">
        <xsl:element name="mmd:temporal_extent">
	    <!--if element is datetime use it, if it is only date add time-->
            <xsl:element name="mmd:start_date">
	       <xsl:choose>
	          <xsl:when test="string-length(mmd:start_date) &gt; 10">
                     <xsl:value-of select="mmd:start_date" />
                  </xsl:when>
	          <xsl:otherwise test="string-length(mmd:start_date) &gt; 10">
                     <xsl:value-of select="concat(mmd:start_date,'T12:00:00Z')" />
                  </xsl:otherwise>
               </xsl:choose>
            </xsl:element>
	    <!--if end_date is not present skip this element-->
	    <xsl:if test="mmd:end_date !=''">
            <xsl:element name="mmd:end_date">
	       <xsl:choose>
	          <xsl:when test="string-length(mmd:end_date) &gt; 10">
                     <xsl:value-of select="mmd:end_date" />
                  </xsl:when>
	          <xsl:otherwise test="string-length(mmd:end_date) &gt; 10">
                     <xsl:value-of select="concat(mmd:end_date,'T12:00:00Z')" />
                  </xsl:otherwise>
               </xsl:choose>
            </xsl:element>
            </xsl:if>
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:iso_topic_category">
      <xsl:element name="mmd:iso_topic_category">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:keywords">
      <xsl:element name="mmd:keywords">
        <xsl:attribute name="vocabulary">
          <xsl:value-of select="@vocabulary" />
        </xsl:attribute>
	<xsl:for-each select="mmd:keyword">
        <xsl:element name="mmd:keyword">
          <xsl:value-of select="." />
        </xsl:element>
        </xsl:for-each>
        <xsl:element name="mmd:resource">
          <xsl:value-of select="mmd:reference" />
        </xsl:element>
        <xsl:element name="mmd:separator">
          <xsl:value-of select="mmd:separator" />
        </xsl:element>
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:operational_status">
      <xsl:element name="mmd:operational_status">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:dataset_language">
      <xsl:element name="mmd:dataset_language">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:access_constraint">
      <xsl:element name="mmd:access_constraint">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

     <xsl:template match="mmd:use_constraint">
        <xsl:element name="mmd:use_constraint">
              <xsl:if test=". = 'Public domain'">
		 <xsl:element name="mmd:identifier">
                    <xsl:text>CC0-1.0</xsl:text>
	         </xsl:element>
		 <xsl:element name="mmd:resource">
                    <xsl:text>http://spdx.org/licenses/CC0-1.0</xsl:text>
	         </xsl:element>
              </xsl:if>
              <xsl:if test=".  ='Attribution'">
		 <xsl:element name="mmd:identifier">
                    <xsl:text>CC-BY-4.0</xsl:text>
	         </xsl:element>
		 <xsl:element name="mmd:resource">
                    <xsl:text>http://spdx.org/licenses/CC-BY-4.0</xsl:text>
	         </xsl:element>
              </xsl:if>
              <xsl:if test=". = 'Share-alike'">
		 <xsl:element name="mmd:identifier">
                    <xsl:text>CC-BY-SA-4.0</xsl:text>
	         </xsl:element>
		 <xsl:element name="mmd:resource">
                    <xsl:text>http://spdx.org/licenses/CC-BY-SA-4.0</xsl:text>
	         </xsl:element>
              </xsl:if>
              <xsl:if test=".='Noncommercial'">
		 <xsl:element name="mmd:identifier">
                    <xsl:text>CC-BY-NC-4.0</xsl:text>
	         </xsl:element>
		 <xsl:element name="mmd:resource">
                    <xsl:text>http://spdx.org/licenses/CC-BY-NC-4.0</xsl:text>
	         </xsl:element>
              </xsl:if>
            </xsl:element>
     </xsl:template>

    <xsl:template match="mmd:project">
        <xsl:element name="mmd:project">
           <xsl:element name="mmd:short_name">
               <xsl:value-of select="mmd:short_name"/>
           </xsl:element>
           <xsl:element name="mmd:long_name">
               <xsl:value-of select="mmd:long_name"/>
           </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:activity_type">
      <xsl:element name="mmd:activity_type">
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:platform">
      <xsl:element name="mmd:platform">
         <xsl:if test="mmd:short_name = 'S1A'">
            <xsl:element name="mmd:short_name">
               <xsl:text>S1A</xsl:text>
	    </xsl:element>
            <xsl:element name="mmd:long_name">
               <xsl:text>Sentinel-1A</xsl:text>
            </xsl:element>
	    <xsl:element name="mmd:resource">
               <xsl:text>https://www.wmo-sat.info/oscar/satellites/view/396</xsl:text>
	    </xsl:element>
         </xsl:if>
         <xsl:if test="mmd:short_name = 'S1B'">
            <xsl:element name="mmd:short_name">
               <xsl:text>S1B</xsl:text>
	    </xsl:element>
            <xsl:element name="mmd:long_name">
               <xsl:text>Sentinel-1B</xsl:text>
            </xsl:element>
	    <xsl:element name="mmd:resource">
               <xsl:text>https://www.wmo-sat.info/oscar/satellites/view/397</xsl:text>
	    </xsl:element>
         </xsl:if>
         <xsl:if test="mmd:short_name = 'S2A'">
            <xsl:element name="mmd:short_name">
               <xsl:text>S2A</xsl:text>
	    </xsl:element>
            <xsl:element name="mmd:long_name">
               <xsl:text>Sentinel-2A</xsl:text>
            </xsl:element>
	    <xsl:element name="mmd:resource">
               <xsl:text>https://www.wmo-sat.info/oscar/satellites/view/398</xsl:text>
	    </xsl:element>
         </xsl:if>
         <xsl:if test="mmd:short_name = 'S2B'">
            <xsl:element name="mmd:short_name">
               <xsl:text>S2B</xsl:text>
	    </xsl:element>
            <xsl:element name="mmd:long_name">
               <xsl:text>Sentinel-2B</xsl:text>
            </xsl:element>
	    <xsl:element name="mmd:resource">
               <xsl:text>https://www.wmo-sat.info/oscar/satellites/view/399</xsl:text>
	    </xsl:element>
         </xsl:if>
         <xsl:if test="mmd:short_name = 'S3A'">
            <xsl:element name="mmd:short_name">
               <xsl:text>S3A</xsl:text>
	    </xsl:element>
            <xsl:element name="mmd:long_name">
               <xsl:text>Sentinel-3A</xsl:text>
            </xsl:element>
	    <xsl:element name="mmd:resource">
               <xsl:text>https://www.wmo-sat.info/oscar/satellites/view/400</xsl:text>
	    </xsl:element>
         </xsl:if>
         <xsl:if test="mmd:short_name = 'S3B'">
            <xsl:element name="mmd:short_name">
               <xsl:text>S3B</xsl:text>
	    </xsl:element>
            <xsl:element name="mmd:long_name">
               <xsl:text>Sentinel-3B</xsl:text>
            </xsl:element>
	    <xsl:element name="mmd:resource">
               <xsl:text>https://www.wmo-sat.info/oscar/satellites/view/802</xsl:text>
	    </xsl:element>
         </xsl:if>
         <xsl:element name="mmd:instrument">
		 <xsl:call-template name="instrument"/>
         </xsl:element>
         <xsl:element name="mmd:ancillary">
		 <xsl:call-template name="ancillary"/>
         </xsl:element>
      </xsl:element>
    </xsl:template>

    <xsl:template name="instrument">
       <xsl:if test="../mmd:instrument/mmd:short_name = 'C-SAR'">
               <xsl:element name="mmd:short_name">
             <xsl:text>SAR-C</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:long_name">
             <xsl:text>Synthetic Aperture Radar (C-band)</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:resource">
             <xsl:text>https://www.wmo-sat.info/oscar/instruments/view/312</xsl:text>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:instrument/mmd:short_name = 'MSI'">
          <xsl:element name="mmd:short_name">
             <xsl:text>MSI</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:long_name">
             <xsl:text>Multi-Spectral Imager for Sentinel-2</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:resource">
             <xsl:text>https://www.wmo-sat.info/oscar/instruments/view/312</xsl:text>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:instrument/mmd:short_name = 'OLCI'">
          <xsl:element name="mmd:short_name">
             <xsl:text>OLCI</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:long_name">
             <xsl:text>Ocean and Land Colour Imager</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:resource">
             <xsl:text>https://www.wmo-sat.info/oscar/instruments/view/374</xsl:text>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:instrument/mmd:short_name = 'SLSTR'">
          <xsl:element name="mmd:short_name">
             <xsl:text>SLSTR</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:long_name">
             <xsl:text>Sea and Land Surface Temperature Radiometer</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:resource">
             <xsl:text>https://www.wmo-sat.info/oscar/instruments/view/518</xsl:text>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:instrument/mmd:short_name = 'MWR'">
          <xsl:element name="mmd:short_name">
             <xsl:text>MWR</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:long_name">
             <xsl:text>Micro-Wave Radiometer</xsl:text>
          </xsl:element>
          <xsl:element name="mmd:resource">
             <xsl:text>https://www.wmo-sat.info/oscar/instruments/view/348</xsl:text>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:instrument/mmd:mode = 'SM' or ../mmd:instrument/mmd:mode = 'IW' or ../mmd:instrument/mmd:mode = 'EW' or ../mmd:instrument/mmd:mode = 'VW'">
          <xsl:element name="mmd:mode">
             <xsl:value-of select="../mmd:instrument/mmd:mode"/>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:instrument/mmd:polarisation !=''">
          <xsl:element name="mmd:polarisation">
             <xsl:value-of select="../mmd:instrument/mmd:polarisation"/>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:instrument/mmd:product_type !=''">
          <xsl:element name="mmd:product_type">
             <xsl:value-of select="../mmd:instrument/mmd:product_type"/>
          </xsl:element>
       </xsl:if>
    </xsl:template>

    <xsl:template name="ancillary">
       <xsl:if test="../mmd:cloud_coverage !=''">
          <xsl:element name="mmd:cloud_coverage">
             <xsl:value-of select="../mmd:cloud_cover/mmd:value"/>
          </xsl:element>
       </xsl:if>
       <xsl:if test="../mmd:scene_coverage !=''">
          <xsl:element name="mmd:scene_coverage">
             <xsl:value-of select="../mmd:scene_cover/mmd:value"/>
          </xsl:element>
       </xsl:if>
    </xsl:template>


    <xsl:template match="mmd:related_information">
        <xsl:element name="mmd:related_information">
           <xsl:element name="mmd:type">
               <xsl:value-of select="mmd:type"/>
           </xsl:element>
           <xsl:element name="mmd:description">
               <xsl:value-of select="mmd:description"/>
           </xsl:element>
           <xsl:element name="mmd:resource">
               <xsl:value-of select="mmd:resource"/>
           </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:personnel">
        <xsl:element name="mmd:personnel">
           <xsl:element name="mmd:role">
               <xsl:value-of select="mmd:role"/>
           </xsl:element>
           <xsl:element name="mmd:name">
               <xsl:value-of select="mmd:name"/>
           </xsl:element>
           <xsl:element name="mmd:email">
               <xsl:value-of select="mmd:email"/>
           </xsl:element>
           <xsl:element name="mmd:phone">
               <xsl:value-of select="mmd:phone"/>
           </xsl:element>
           <xsl:element name="mmd:fax">
               <xsl:value-of select="mmd:fax"/>
           </xsl:element>
           <xsl:element name="mmd:organisation">
               <xsl:value-of select="mmd:organisation"/>
           </xsl:element>
           <xsl:element name="mmd:contact_address">
           <xsl:element name="mmd:address">
		   <xsl:value-of select="mmd:contact_address/mmd:address"/>
           </xsl:element>
           <xsl:element name="mmd:city">
               <xsl:value-of select="mmd:contact_address/mmd:city"/>
           </xsl:element>
           <xsl:element name="mmd:province_or_state">
               <xsl:value-of select="mmd:contact_address/mmd:province_or_state"/>
           </xsl:element>
           <xsl:element name="mmd:postal_code">
               <xsl:value-of select="mmd:contact_address/mmd:postal_code"/>
           </xsl:element>
           <xsl:element name="mmd:country">
               <xsl:value-of select="mmd:contact_address/mmd:country"/>
           </xsl:element>
           </xsl:element>
        </xsl:element>
    </xsl:template>


    <xsl:template match="mmd:dataset_citation">
       <xsl:element name="mmd:dataset_citation">
          <xsl:copy-of select="."/>
       </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:data_access">
        <xsl:element name="mmd:data_access">
           <xsl:element name="mmd:name">
               <xsl:value-of select="mmd:name"/>
           </xsl:element>
           <xsl:element name="mmd:type">
               <xsl:value-of select="mmd:type"/>
           </xsl:element>
           <xsl:element name="mmd:description">
               <xsl:value-of select="mmd:description"/>
           </xsl:element>
           <xsl:element name="mmd:resource">
               <xsl:value-of select="mmd:resource"/>
           </xsl:element>
           <xsl:element name="mmd:wms_layers">
		   <xsl:for-each select="mmd:wms_layers/mmd:wms_layer">
                   <xsl:element name="mmd:wms_layer">
		      <xsl:value-of select="." />
                   </xsl:element>
                </xsl:for-each>
           </xsl:element>
        </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:data_center">
       <xsl:element name="mmd:data_center">
          <xsl:element name="mmd:data_center_name">
          <xsl:element name="mmd:short_name">
             <xsl:value-of select="mmd:data_center_name/mmd:short_name"/>
          </xsl:element>
          <xsl:element name="mmd:long_name">
             <xsl:value-of select="mmd:data_center_name/mmd:long_name"/>
          </xsl:element>
          </xsl:element>
          <xsl:element name="mmd:data_center_url">
             <xsl:value-of select="mmd:data_center_url"/>
          </xsl:element>
       </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:related_dataset">
      <xsl:element name="mmd:related_dataset">
	      <xsl:attribute name="mmd:relation_type">
		 <xsl:value-of select="@mmd:relation_type" />
	      </xsl:attribute>
          <xsl:value-of select="." />
      </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:geographic_extent/mmd:rectangle">
       <xsl:element name="mmd:geographic_extent">
           <xsl:element name="mmd:rectangle">
	      <xsl:attribute name="srsName">
                 <xsl:value-of select="@srsName"/>
              </xsl:attribute>
              <xsl:element name="mmd:north">
                  <xsl:value-of select="mmd:north"/>
              </xsl:element>
              <xsl:element name="mmd:south">
                  <xsl:value-of select="mmd:south"/>
              </xsl:element>
              <xsl:element name="mmd:west">
                  <xsl:value-of select="mmd:west"/>
              </xsl:element>
              <xsl:element name="mmd:east">
                  <xsl:value-of select="mmd:east"/>
              </xsl:element>
           </xsl:element>
       </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:geographic_extent/mmd:polygon">
       <xsl:element name="mmd:geographic_extent">
          <xsl:element name="mmd:polygon">
  	     <xsl:copy-of select="gml:Polygon"/>
          </xsl:element>
       </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:system_specific_product_category">
       <xsl:element name="mmd:system_specific_product_category">
          <xsl:copy-of select="."/>
       </xsl:element>
    </xsl:template>

    <xsl:template match="mmd:system_specific_product_relevance">
       <xsl:element name="mmd:system_specific_product_relevance">
          <xsl:copy-of select="."/>
       </xsl:element>
    </xsl:template>

</xsl:stylesheet>
