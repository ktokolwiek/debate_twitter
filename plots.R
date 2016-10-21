library(ggplot2)
library(zoo)
library(scales)
library(plotly)
Sys.setenv(TZ='America/Los_Angeles')
cbPalette <- c("#999999", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7")  # colour-blind palette


df <- read.csv('output/data.csv')
df$created_at <- as.POSIXct(as.character(df$created_at), format = '%a %b %d %H:%M:%S %z %Y',tz="America/Los_Angeles")
attributes(df$created_at)$tzone <- "America/Los_Angeles"
df$has_trump <- as.factor(df$has_trump)
df$has_hombres <- as.factor(df$has_hombres)
df$has_hillary <- as.factor(df$has_hillary)
df$has_candidate <- as.factor(as.numeric(df$has_trump) + as.numeric(df$has_hillary))

m.av<-rollmean(zoo(df$sentiment), 3,fill = list(NA, NULL, NA))

debate_time <- data.frame(xmin=as.POSIXct("2016-10-19 18:00:00", tz="America/Los_Angeles"),
                          xmax=as.POSIXct("2016-10-19 19:30:00", tz="America/Los_Angeles"),
                          ymin=-Inf, ymax=Inf)
debate_time_box <- geom_rect(data=debate_time, aes(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax),
                             color="grey20",
                             alpha=0.5,
                             inherit.aes = FALSE) 

plot_theme <- theme(panel.border = element_blank(),
                    legend.key = element_blank(),
                    #axis.ticks = element_blank(),
                    #panel.grid = element_blank(),
                    axis.text.x = element_text(angle = 70, vjust = 0.5, hjust=0.5),
                    panel.grid.minor = element_blank(), 
                    panel.grid.major = element_line(colour = '#eeeeee', size=0.1),
                    panel.background = element_blank(),
                    plot.background = element_rect(fill = "transparent",colour = NA),
                    plot.title = element_text(lineheight=.8, face="bold"),
                    legend.justification=c(0,1), legend.position=c(0.1,.9))

hombres_present <- ggplot(data=df, aes(x=created_at, color=has_hombres, fill=has_hombres)) +
  geom_histogram(position = position_dodge(), bins = 60) +
  ggtitle("Bad Hombres only start appearing\nwhen called out...") + 
  scale_x_datetime(limits = c(as.POSIXct("2016-10-19 18:00:00", tz="America/Los_Angeles"),
                              as.POSIXct("2016-10-20 00:30:00", tz="America/Los_Angeles"))) + xlab("") + ylab("Tweets") +
  scale_fill_manual(name="Talking about\nHombres?",
                    labels=c('no', 'yes'),
                    values=cbPalette) +
  scale_color_manual(name="Talking about\nHombres?",
                     labels=c('no', 'yes'),
                     values=cbPalette) + 
  debate_time_box + plot_theme + theme(legend.position = c(0.75, 1))
gg <- ggplotly(hombres_present)
  
ggplot(data=df, aes(x=created_at, color=has_hillary, fill=has_hillary)) +
  geom_histogram(position = position_dodge(), bins=80) +
  scale_x_datetime() +
  ggtitle("Both Hillary...") +
  xlab("") + ylab("Tweets/half hour") +
  scale_fill_manual(name="Talking about Hillary?",
                    labels=c('no', 'yes'),
                    values=cbPalette) +
  scale_color_manual(name="Talking about Hillary?",
                     labels=c('no', 'yes'),
                     values=cbPalette) + 
  debate_time_box + plot_theme

ggplot(data=df, aes(x=created_at, color=has_trump, fill=has_trump)) +
  geom_histogram(position = position_dodge(), bins=80) +
  scale_x_datetime() +
  xlab("") + ylab("Tweets/half hour") +
  ggtitle("and Donald are mentioned\n~equally frequently") +
  scale_fill_manual(name="Talking about Trump?",
                    labels=c('no', 'yes'),
                    values=cbPalette) +
  scale_color_manual(name="Talking about Trump?",
                     labels=c('no', 'yes'),
                     values=cbPalette) + 
  debate_time_box + plot_theme

ggplot(data=df, aes(x=created_at, color=has_candidate, fill=has_candidate)) +
  geom_histogram(position = position_dodge(), bins=80) +
  scale_x_datetime() +
  ggtitle("They also co-occur") +
  xlab("") + ylab("Tweets/half hour") +
  scale_fill_manual(name="Talking about either?",
                    labels=c('none', 'one', 'both'),
                    values=cbPalette) +
  scale_color_manual(name="Talking about either?",
                     labels=c('none', 'one', 'both'),
                     values=cbPalette) + 
  debate_time_box + plot_theme

ggplot(data=df, aes(x=created_at, y=sentiment, color=has_hillary)) +
  stat_smooth(alpha=0.2) +
  scale_color_manual(name="Talking about Hillary?",
                     labels=c('no', 'yes'),
                     values=cbPalette) + 
  debate_time_box + plot_theme +
  scale_x_datetime() + xlab("") + ylab("Sentiment Valence") + coord_cartesian(ylim=c(2.5,5)) + theme(legend.position = c(.1, .4))


ggplot(data=df, aes(x=created_at, y=sentiment, color=has_trump)) +
  stat_smooth(alpha=0.2) +
  scale_color_manual(name="Talking about Trump?",
                     labels=c('no', 'yes'),
                     values=cbPalette) +
  debate_time_box + plot_theme +
  scale_x_datetime() + xlab("") + ylab("Sentiment Valence") + coord_cartesian(ylim=c(2.5,5)) + theme(legend.position = c(.1, .4))

ggplot(data=df, aes(x=created_at, y=sentiment, color=has_candidate)) +
  stat_smooth(alpha=0.2) +
  scale_color_manual(name="Talking about either?",
                     labels=c('none', 'one', 'both'),
                     values=cbPalette) +
  debate_time_box + plot_theme +
  scale_x_datetime() + xlab("") + ylab("Sentiment Valence") + coord_cartesian(ylim=c(2.5,5)) + theme(legend.position = c(.1, .4))


ggplot(data=df, aes(x=created_at, y=sentiment, color=has_hombres)) +
  stat_smooth(alpha=0.2) +
  ggtitle("But when they do, they are some bad hombres!") +
  geom_rect(data=debate_time, aes(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax),
            color="grey20",
            alpha=0.5,
            inherit.aes = FALSE) +
  scale_color_manual(name="Talking about Hombres?",
                     labels=c('no', 'yes'),
                     values=cbPalette) + 
  scale_x_datetime(limits = c(as.POSIXct("2016-10-19 18:00:00", tz="America/Los_Angeles"),
                              as.POSIXct("2016-10-20 00:30:00", tz="America/Los_Angeles"))) +
  plot_theme + xlab("") + ylab("Sentiment Valence") + theme(legend.position = c(0.3, 0.7)) + coord_cartesian(ylim=c(2.5,5))