.PHONY: download-data clean-data

DATA_DIR := data
TRAIN_ZIP := $(DATA_DIR)/grayscale-train.zip
TEST_ZIP := $(DATA_DIR)/grayscale-test.zip
TRAIN_DIR := $(DATA_DIR)/train
TEST_DIR := $(DATA_DIR)/test
GRAYSCALE_TRAIN_URL := https://raw.githubusercontent.com/alvarobartt/simpsons-mnist/master/dataset/grayscale-train.zip
GRAYSCALE_TEST_URL := https://raw.githubusercontent.com/alvarobartt/simpsons-mnist/master/dataset/grayscale-test.zip

# Default target to fetch and unpack the grayscale dataset splits
download-data: $(TRAIN_DIR) $(TEST_DIR)

$(TRAIN_ZIP):
	mkdir -p $(DATA_DIR)
	curl -L -o $@ $(GRAYSCALE_TRAIN_URL)

$(TEST_ZIP):
	mkdir -p $(DATA_DIR)
	curl -L -o $@ $(GRAYSCALE_TEST_URL)

# Extract the grayscale training split into data/train
$(TRAIN_DIR): $(TRAIN_ZIP)
	unzip -q -o $< -d $(DATA_DIR)
	@if [ -d $(DATA_DIR)/grayscale-train ]; then mv $(DATA_DIR)/grayscale-train $@; fi
	@if [ -d $(DATA_DIR)/grayscale/train ]; then mv $(DATA_DIR)/grayscale/train $@; fi
	@if [ -d $(DATA_DIR)/train ] && [ ! -d $@ ]; then mv $(DATA_DIR)/train $@; fi

# Extract the grayscale test split into data/test
$(TEST_DIR): $(TEST_ZIP)
	unzip -q -o $< -d $(DATA_DIR)
	@if [ -d $(DATA_DIR)/grayscale-test ]; then mv $(DATA_DIR)/grayscale-test $@; fi
	@if [ -d $(DATA_DIR)/grayscale/test ]; then mv $(DATA_DIR)/grayscale/test $@; fi
	@if [ -d $(DATA_DIR)/test ] && [ ! -d $@ ]; then mv $(DATA_DIR)/test $@; fi

# Remove downloaded archives and extracted splits
clean-data:
	rm -rf $(TRAIN_DIR) $(TEST_DIR) $(TRAIN_ZIP) $(TEST_ZIP)

